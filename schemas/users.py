from typing import Annotated, Optional
from fastapi import UploadFile, File
from pydantic import BaseModel, StringConstraints, ConfigDict, field_validator
from pydantic import EmailStr
import re

class UsersCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    login: Annotated[str, StringConstraints(min_length=6, max_length=16)]
    password: Annotated[str, StringConstraints(min_length=10, max_length=32)]
    email: EmailStr
    name: Annotated[str, StringConstraints(min_length=5, max_length=16)]

    @field_validator("password")
    @classmethod

    def pwdval(cls, v):
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v) or not re.search(r"[0-9]", v) or not re.search(r"[~!@#$%^&*()_+]", v):
            raise ValueError("Password must be at least 10 characters long. Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number and 1 special character (~!@#$%^&*()_+)")
        return v

class UsersEdit(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Annotated[Optional[str], StringConstraints(min_length=5, max_length=16)] = None
    pfp: Annotated[Optional[UploadFile | None], File()] = None

    @field_validator("name")
    @classmethod

    def empty_to_str(cls, v: str):
        if v == "":
            return None
        return v

class PasswordReset(BaseModel):
    password: Annotated[str, StringConstraints(min_length=10, max_length=32)]

    @field_validator("password")
    @classmethod
    def pwdval(cls, v):
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v) or not re.search(r"[0-9]", v) or not re.search(
                r"[~!@#$%^&*()_+]", v):
            raise ValueError(
                "Password must be at least 10 characters long. Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number and 1 special character (~!@#$%^&*()_+)")
        return v