"""Hash de senhas, emissão/validação de JWT e limitador de tentativas."""

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings

settings = get_settings()

# Hash fixo usado quando o e-mail não existe, para que o tempo de resposta
# do login não revele se a conta está cadastrada (evita enumeração).
_DUMMY_HASH = bcrypt.hashpw(b"senha-ficticia", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    """Gera o hash bcrypt (com salt) da senha."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    """Confere a senha em tempo constante."""
    target = (password_hash or _DUMMY_HASH).encode("utf-8")
    matches = bcrypt.checkpw(password.encode("utf-8"), target)
    return matches and password_hash is not None


def create_access_token(user_id: int) -> str:
    """Cria um JWT assinado para o usuário informado."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> int | None:
    """Valida o token e retorna o id do usuário, ou None se inválido."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            # Lista explícita impede ataques de troca de algoritmo ("none").
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub", "iat"]},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        return None


class RateLimiter:
    """Limitador simples em memória por chave (ex.: IP), janela deslizante.

    Suficiente para uma instância única. Em produção com várias instâncias,
    usar um armazenamento compartilhado (ex.: Redis).
    """

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        """Registra uma tentativa; retorna False se o limite foi excedido."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.max_attempts:
                return False
            hits.append(now)
            return True

    def reset(self, key: str | None = None) -> None:
        """Limpa as tentativas de uma chave (ou de todas)."""
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)


login_limiter = RateLimiter(
    settings.login_rate_limit, settings.login_rate_window_seconds
)
