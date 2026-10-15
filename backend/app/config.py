"""Configurações da aplicação carregadas de variáveis de ambiente / .env."""

import secrets
import warnings
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT = "troque-esta-chave-por-uma-chave-aleatoria-e-longa"


class Settings(BaseSettings):
    """Valores configuráveis da API."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "To-Do API"
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./todo.db"
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"
    login_rate_limit: int = 5
    login_rate_window_seconds: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        """Converte a string de origens em lista."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retorna as configurações (instância única, em cache).

    Se nenhuma SECRET_KEY segura for definida, gera uma aleatória para a
    execução atual. Os tokens deixam de valer ao reiniciar o servidor, o que
    é aceitável em desenvolvimento, mas nunca em produção.
    """
    settings = Settings()
    if not settings.secret_key or settings.secret_key == _INSECURE_DEFAULT:
        warnings.warn(
            "SECRET_KEY não definida: usando chave temporária. "
            "Defina SECRET_KEY no arquivo .env.",
            stacklevel=2,
        )
        settings.secret_key = secrets.token_urlsafe(64)
    return settings
