from pydantic import BaseModel


class Config(BaseModel):
    window: dict[str, dict[str, int]]
