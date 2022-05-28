from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    has_foul_language = Column(Boolean)

    paragraphs = relationship("Paragraph", back_populates="post")


class Paragraph(Base):
    __tablename__ = "paragraphs"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    blog_post_id = Column(Integer, ForeignKey("blog_posts.id"))

    post = relationship("BlogPost", back_populates="paragraphs")
