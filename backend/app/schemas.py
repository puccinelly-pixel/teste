"""Schemas Pydantic de entrada e saída da API."""

import re
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.models import TaskStatus

# ---------------------------------------------------------------------------
# Usuários / autenticação
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Dados para cadastro de usuário."""

    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)

    @field_validator("nome")
    @classmethod
    def _strip_nome(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("O nome deve ter pelo menos 2 caracteres.")
        return value

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("senha")
    @classmethod
    def _senha_forte(cls, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("A senha deve conter letras e números.")
        # O bcrypt considera no máximo 72 bytes (acentos ocupam 2 bytes).
        if len(value.encode("utf-8")) > 72:
            raise ValueError("A senha é longa demais.")
        return value


class UserLogin(BaseModel):
    """Credenciais de login."""

    email: EmailStr
    senha: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return value.lower()


class UserOut(BaseModel):
    """Dados públicos do usuário."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    data_criacao: datetime


class Token(BaseModel):
    """Resposta de autenticação."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UserOut


# ---------------------------------------------------------------------------
# Tarefas
# ---------------------------------------------------------------------------


def _clean_titulo(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("O título não pode ficar em branco.")
    return value


class TaskCreate(BaseModel):
    """Dados para criar uma tarefa."""

    titulo: str = Field(min_length=1, max_length=120)
    descricao: str | None = Field(default=None, max_length=1000)
    status: TaskStatus = TaskStatus.PENDENTE

    @field_validator("titulo")
    @classmethod
    def _titulo(cls, value: str) -> str:
        return _clean_titulo(value)


class TaskUpdate(BaseModel):
    """Atualização parcial de uma tarefa (todos os campos opcionais)."""

    titulo: str | None = Field(default=None, min_length=1, max_length=120)
    descricao: str | None = Field(default=None, max_length=1000)
    status: TaskStatus | None = None

    @field_validator("titulo")
    @classmethod
    def _titulo(cls, value: str | None) -> str | None:
        return None if value is None else _clean_titulo(value)


class TaskOut(BaseModel):
    """Representação de uma tarefa nas respostas."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str | None
    status: TaskStatus
    data_criacao: datetime
    data_atualizacao: datetime


class TaskList(BaseModel):
    """Lista paginada de tarefas."""

    total: int
    limit: int
    offset: int
    items: list[TaskOut]
