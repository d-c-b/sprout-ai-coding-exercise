import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base
from src.main import app, get_db
from src import models

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


def test_create_blog_post(test_db):
    response = client.post(
        "/posts/",
        json={
            "title": "This is an engaging title",
            "paragraphs": [
                "This is the first paragraph. It contains two sentences.",
                "This is the second parapgraph. It contains two more sentences",
                "Third paraphraph here.",
            ],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "This is an engaging title"
    assert data["has_foul_language"] is None
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


def test_get_blog_post(test_db):
    # Create post using the creat post request
    create_response = client.post(
        "/posts/",
        json={
            "title": "This is an engaging title",
            "paragraphs": [
                "This is the first paragraph. It contains two sentences.",
                "This is the second parapgraph. It contains two more sentences",
                "Third paraphraph here.",
            ],
        },
    )
    assert create_response.status_code == 200
    post_id = create_response.json()["id"]

    get_response = client.get(f"/posts/{post_id}")

    assert get_response.status_code == 200, get_response.text
    data = get_response.json()
    assert data["id"] == post_id
    assert data["title"] == "This is an engaging title"
    assert data["has_foul_language"] is None
    assert data["paragraphs"] == [
        "This is the first paragraph. It contains two sentences.",
        "This is the second parapgraph. It contains two more sentences",
        "Third paraphraph here.",
    ]
