import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    last_name: str = Field(..., description="Фамилия пользователя")
    first_name: str = Field(..., description="Имя пользователя")
    middle_name: str | None = Field(None, description="Отчество пользователя")
    iin: str = Field(..., description="ИИН пользователя")
    phone_number: str = Field(..., description="Номер телефона пользователя")
    photo_url: str | None = Field(None, description="URL на фото пользователя")

    @field_validator("iin")
    def validate_iin(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 12:
            raise ValueError("ИИН должен состоять из 12 цифр")
        return v

    @field_validator("phone_number")
    def validate_phone_number(cls, v: str) -> str:
        pattern = re.compile(r"^\+7\s?7\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$")
        if not pattern.match(v):
            raise ValueError(
                "Номер телефона должен соответствовать формату +7 7XX XXX XX XX"
            )
        return "".join(v.split())


class UserUpdate(BaseModel):
    last_name: str | None = Field(None, description="Фамилия пользователя")
    first_name: str | None = Field(None, description="Имя пользователя")
    middle_name: str | None = Field(None, description="Отчество пользователя")
    iin: str | None = Field(None, description="ИИН пользователя")
    phone_number: str | None = Field(None, description="Мобильный номер пользователя")
    photo_url: str | None = Field(None, description="Личное фото пользователя")


    @field_validator("iin")
    @classmethod
    def validate_iin(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not v.isdigit() or len(v)!=12:
            raise ValueError('ИИН должен состоять ровно из 12 цифр')
        return v
    

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        if v is None:
            return None
        pattern = re.compile(r'^\+7\s?7\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$')
        if not pattern.match(v):
            raise ValueError('Номер телефона должен быть в формате +77xxAAABBCC')
        return "".join(v.split())


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: str = Field(..., description="Уникальный идентификатор пользователя")


SUPPORTED_DOC_TYPES = Literal["pdf", "docx", "doc"]


class DocumentRequest(BaseModel):
    user_id: str
    content_type: SUPPORTED_DOC_TYPES


class AsyncDocumentRequest(DocumentRequest):
    callback_url: str = Field(
        ..., description="URL для отправки результата обработки документа"
    )


class DocumentResponse(BaseModel):
    message: str
    document_url: str | None = None


class TaskAccepted(BaseModel):
    message: str
