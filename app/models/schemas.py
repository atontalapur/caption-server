from pydantic import BaseModel
from typing import List


class CaptionResponse(BaseModel):
    captions: List[str]
    style_samples_loaded: int


class HealthResponse(BaseModel):
    status: str
    writings_loaded: int
    port: int
