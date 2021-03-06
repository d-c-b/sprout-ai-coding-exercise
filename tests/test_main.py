import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base
from src.main import app, get_db, serialize_blog_post
from src import models
import requests

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


mock_blog_post_body = {
    "title": "This is an engaging title",
    "paragraphs": [
        "This is the first paragraph. It contains two sentences.",
        "This is the second parapgraph. It contains two more sentences",
        "Third paraphraph here.",
    ],
}


def test_create_blog_post(test_db):
    response = client.post(
        "/posts/",
        json=mock_blog_post_body,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "This is an engaging title"
    assert data["has_foul_language"] is False
    expected_paragraphs = [
        "This is the first paragraph. It contains two sentences.",
        "This is the second parapgraph. It contains two more sentences",
        "Third paraphraph here.",
    ]
    assert data["paragraphs"] == expected_paragraphs
    assert "id" in data
    db = next(override_get_db())

    db_blog_posts_query = db.query(models.BlogPost).where(
        models.BlogPost.title == "This is an engaging title"
    )
    assert db_blog_posts_query.count() == 1
    db_post = db_blog_posts_query.first()
    assert len(db_post.paragraphs) == 3
    assert list(map(lambda p: p.text, db_post.paragraphs)) == expected_paragraphs


def test_create_blog_post_with_foul_language(test_db, requests_mock):
    requests_mock.real_http = True

    # mock call to content model service to return True for having foul language
    requests_mock.post(
        "http://content_model_service:9000/sentences/",
        json={"hasFoulLanguage": True},
    )

    response = client.post(
        "/posts/",
        json=mock_blog_post_body,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "This is an engaging title"
    assert data["has_foul_language"] is True
    db = next(override_get_db())
    db_blog_posts_query = db.query(models.BlogPost).where(
        models.BlogPost.title == "This is an engaging title"
    )
    assert db_blog_posts_query.count() == 1
    db_post = db_blog_posts_query.first()
    assert db_post.has_foul_language is True


def test_create_blog_post_content_model_service_unavailable(test_db, requests_mock):
    requests_mock.real_http = True

    # mock call to content model service to return True for having foul language
    requests_mock.post(
        "http://content_model_service:9000/sentences/",
        exc=requests.exceptions.ConnectTimeout,
        # json={"hasFoulLanguage": True},
    )

    response = client.post(
        "/posts/",
        json=mock_blog_post_body,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["has_foul_language"] is None
    db = next(override_get_db())
    db_blog_posts_query = db.query(models.BlogPost).where(
        models.BlogPost.title == "This is an engaging title"
    )
    assert db_blog_posts_query.count() == 1
    db_post = db_blog_posts_query.first()
    assert db_post.has_foul_language is None


def test_get_blog_post(test_db):
    # Create post using the create post request
    create_response = client.post(
        "/posts/",
        json=mock_blog_post_body,
    )
    assert create_response.status_code == 200
    post_id = create_response.json()["id"]

    get_response = client.get(f"/posts/{post_id}")

    assert get_response.status_code == 200, get_response.text
    data = get_response.json()
    assert data["id"] == post_id
    assert data["title"] == "This is an engaging title"
    assert data["has_foul_language"] is False
    assert data["paragraphs"] == [
        "This is the first paragraph. It contains two sentences.",
        "This is the second parapgraph. It contains two more sentences",
        "Third paraphraph here.",
    ]


def test_serialize_blog_post():
    blog_post_model = models.BlogPost(
        title="Another title",
        has_foul_language=False,
        paragraphs=[
            models.Paragraph(text="A first paragraph. Another sentence"),
            models.Paragraph(text="A second paragraph. And another sentence"),
        ],
    )
    serialized = serialize_blog_post(blog_post_model)
    assert serialized["title"] == "Another title"
    assert serialized["has_foul_language"] is False
    assert serialized["paragraphs"] == [
        "A first paragraph. Another sentence",
        "A second paragraph. And another sentence",
    ]


def test_retry_unchecked_posts(test_db):
    db = next(override_get_db())

    # Create blog post with has_foul_language = None
    db_blog_post = models.BlogPost(title="A new title", paragraphs=[models.Paragraph(text="A test paragraph")], has_foul_language=None)
    db.add(db_blog_post)
    db.commit()

    db.refresh(db_blog_post)

    assert db_blog_post.has_foul_language is None

    response = client.post(
        "/retry-unchecked-posts/",
    )
    assert response.status_code == 200
    db.refresh(db_blog_post)

    assert db_blog_post.has_foul_language is False
