from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from . import models, schemas
import re
import requests

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


def serialize_blog_post(db_blog_post: models.BlogPost):
    # map paragraphs back from Foreign Key models to list of strings
    paragraphs = list(
        map(lambda paragraph_model: paragraph_model.text, db_blog_post.paragraphs)
    )
    return dict(
        **{
            k: db_blog_post.__dict__[k]
            for k in db_blog_post.__dict__.keys()
            if k != "paragraphs"
        },
        paragraphs=paragraphs
    )


def check_foul_language(paragraphs: list[str]) -> bool:
    for paragraph in paragraphs:
        # get indices of start of each sentence in the paragraph string
        sentence_start_indices = [0] + list(
            map(lambda x: x.start() + 1, re.finditer(r"\. [A-Z]", paragraph))
        )

        # break paragraph text into chunks based on indices and strip
        # whitespace to get each sentence individually
        sentences = [
            sentence.strip()
            for sentence in [
                paragraph[i:j]
                for i, j in zip(
                    sentence_start_indices, sentence_start_indices[1:] + [None]
                )
            ]
        ]

        for sentence in sentences:
            try:
                res = requests.post(
                    "http://content_model_service:9000/sentences/",
                    json={"fragment": sentence},
                )
                if res.status_code == 200:
                    try:
                        if res.json()["hasFoulLanguage"]:
                            return True
                    except KeyError:
                        return None
                else:
                    return None
            except Exception:
                return None

    return False


@app.post("/posts/")
def create_blog_post(post: schemas.BlogPostCreate, db: Session = Depends(get_db)):
    paragraphs = list(
        map(
            lambda paragraph_text: models.Paragraph(text=paragraph_text),
            post.dict()["paragraphs"],
        )
    )
    has_foul_language = check_foul_language(post.dict()["paragraphs"])
    db_blog_post = models.BlogPost(
        **dict(post.dict(), paragraphs=paragraphs, has_foul_language=has_foul_language)
    )
    db.add(db_blog_post)
    db.commit()
    db.refresh(db_blog_post)

    return serialize_blog_post(db_blog_post)


@app.get("/posts/{post_id}")
def get_blog_post(post_id: int, db: Session = Depends(get_db)):
    db_blog_post = db.query(models.BlogPost).get(post_id)

    return serialize_blog_post(db_blog_post)
