"""
Configurações da API, lidas de variáveis de ambiente (ou de um arquivo .env local).
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_name: str = "LMS RPA Monitor API"
    api_prefix: str = "/api"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/lms_legal"

    # Lista separada por vírgulas: ng serve (4200) e o front servido pelo Nginx (8080)
    cors_origins: str = "http://localhost:4200,http://localhost:8080"

    # "simulated": dados fictícios + simulador ao vivo (demonstração).
    # "real": só o robô grava execuções e contratos; sem seed, sem agenda fictícia e sem disparo pelo painel.
    rpa_mode: Literal["simulated", "real"] = "simulated"
    # Token que o robô envia no cabeçalho X-RPA-Token. Vazio = rotas /api/rpa/ desativadas.
    rpa_api_token: str = ""

    # Simulador do RPA (usado no modo "simulated")
    seed_on_startup: bool = True  # popula o histórico fictício se o banco estiver vazio
    seed_days: int = 30
    simulator_failure_rate: float = 0.12
    simulator_speed: float = 1.0  # 2.0 = execução ao vivo duas vezes mais rápida
    simulator_scheduler_enabled: bool = True
    simulator_schedule: str = "08:00,12:00,18:00"

    running_rate_target: float = 85

    @property
    def simulated(self) -> bool:
        return self.rpa_mode == "simulated"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
