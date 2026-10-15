"""Rotas de cadastro, login e dados do usuário logado."""

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserOut
from app.security import (
    create_access_token,
    hash_password,
    login_limiter,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])
settings = get_settings()


def _token_response(user: User) -> Token:
    return Token(
        access_token=create_access_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
        usuario=UserOut.model_validate(user),
    )


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo usuário",
)
def register(payload: UserCreate, db: DbSession) -> Token:
    """Cria a conta e já devolve um token de acesso."""
    user = User(
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este e-mail.",
        ) from None
    db.refresh(user)
    return _token_response(user)


@router.post("/login", response_model=Token, summary="Fazer login")
def login(payload: UserLogin, request: Request, db: DbSession) -> Token:
    """Autentica com e-mail e senha e devolve um token JWT."""
    client_ip = request.client.host if request.client else "desconhecido"
    if not login_limiter.hit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Aguarde um minuto.",
        )

    user = db.scalar(select(User).where(User.email == payload.email))
    # Mesma mensagem para e-mail inexistente e senha errada.
    if not verify_password(payload.senha, user.senha_hash if user else None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    login_limiter.reset(client_ip)
    return _token_response(user)


@router.get("/me", response_model=UserOut, summary="Usuário autenticado")
def me(current_user: CurrentUser) -> User:
    """Retorna os dados do usuário dono do token."""
    return current_user
