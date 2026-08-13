from typing import Annotated, Optional
from fastapi import UploadFile, File
from pydantic import BaseModel, StringConstraints, ConfigDict, field_validator
from pydantic import EmailStr
import re

class PostsCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Annotated[str, StringConstraints(min_length=5, max_length=100)]
    body: Annotated[str, StringConstraints(min_length=5, max_length=5000)]

class PostsUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Annotated[Optional[str], StringConstraints(min_length=5, max_length=100)] = None
    body: Annotated[Optional[str], StringConstraints(min_length=5, max_length=5000)] = None
    allow_comms: bool = False

    @field_validator("title", "body")
    @classmethod
    def empty_to_str(cls, v: str):
        if v == "":
            return None
        return v