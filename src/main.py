from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from . import models, schemas


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


@app.post("/posts/")
def create_blog_post(post: schemas.BlogPostCreate, db: Session = Depends(get_db)):
    paragraphs = list(
        map(
            lambda paragraph_text: models.Paragraph(text=paragraph_text),
            post.dict()["paragraphs"],
        )
    )

    db_blog_post = models.BlogPost(**dict(post.dict(), paragraphs=paragraphs))
    db.add(db_blog_post)
    db.commit()
    db.refresh(db_blog_post)

    return serialize_blog_post(db_blog_post)


@app.get("/posts/{post_id}")
def get_blog_post(post_id: int, db: Session = Depends(get_db)):
    db_blog_post = db.query(models.BlogPost).get(post_id)

    return serialize_blog_post(db_blog_post)


