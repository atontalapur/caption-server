from pydantic import BaseModel
from typing import List


class TrainResponse(BaseModel):
    status: str          # "ready"
    files_accepted: int
    message: str


class CaptionResponse(BaseModel):
    captions: List[str]
    style_samples_loaded: int


class HealthResponse(BaseModel):
    status: str          # "ok"
    trained: bool
    files_loaded: int
    port: int
