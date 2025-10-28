import re
from pydantic import BaseModel, Field, field_validator

class UserBase(BaseModel):
    last_name: str = Field(..., description = "Фамилия пользователя")
    first_name: str = Field(..., description = "Имя пользователя")
    middle_name: str | None = Field(None, description = "Отчество пользователя")
    iin: str = Field(..., description = "ИИН пользователя")
    phone_number: str = Field(..., description = "Номер телефона пользователя")\
    
    @field_validator('iin')
    def validate_iin(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 12:
            raise ValueError('ИИН должен состоять из 12 цифр')
        return v
    @field_validator('phone_number')
    def validate_phone_number(cls, v: str) -> str:
        pattern = re.compile(r'^\+7\s?7\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$')
        if not pattern.match(v):
            raise ValueError('Номер телефона должен соответствовать формату +7 7XX XXX XX XX')
        return "".join(v.split())
    

class UserCreate(UserBase):
    pass


class User(UserBase):
    id: str = Field(..., description = "Уникальный идентификатор пользователя")


class Message(BaseModel):
    message: str = Field(..., description = "Модель для обычных сообщений")
