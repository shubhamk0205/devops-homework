from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # normal settings -> come from a ConfigMap in Kubernetes
    app_name: str = "HelpDesk API"
    app_env: str = "local"
    log_level: str = "INFO"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "helpdesk"

    # credentials -> come from a Secret in Kubernetes (never commit real values)
    db_user: str = "helpdesk"
    db_password: str = "helpdesk"

    # optional full URL (used by the tests with SQLite)
    database_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
