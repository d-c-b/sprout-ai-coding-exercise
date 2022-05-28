from pydantic import BaseModel


class ParagraphBase(BaseModel):
    text: str


class ParagraphCreate(ParagraphBase):
    text: str


class Paragraph(ParagraphBase):
    id: int
    blog_post_id: int

    class Config:
        orm_mode = True


class BlogPostBase(BaseModel):
    title: str


class BlogPostCreate(BlogPostBase):
    paragraphs: list[str]


class BlogPost(BlogPostBase):
    has_foul_language: bool | None
