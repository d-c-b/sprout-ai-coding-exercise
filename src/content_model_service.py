from fastapi import FastAPI

from .ml_content_model_mock import mocked_ml_model_call
from . import schemas

app = FastAPI()


@app.post("/sentences/", response_model=schemas.SentencesResponse)
def call_content_moderation(sentences_body: schemas.SentencesBody):
    has_foul_language = mocked_ml_model_call(sentences_body.fragment)
    return {"hasFoulLanguage": has_foul_language}
