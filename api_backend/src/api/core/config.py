import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _read_db_connection_txt() -> Optional[str]:
    """
    Attempt to read the connection string from resident_db/db_connection.txt.

    The DB container writes a command like:
      psql postgresql://user:pass@localhost:5000/myapp

    We extract the URL part if present.
    """
    # Try multiple plausible relative locations from the backend container.
    candidates = [
        Path(__file__).resolve().parents[4] / "resident_db" / "db_connection.txt",
        Path(__file__).resolve().parents[5] / "resident_db" / "db_connection.txt",
        Path(__file__).resolve().parents[6] / "resident_db" / "db_connection.txt",
    ]

    for p in candidates:
        try:
            if p.exists():
                raw = p.read_text(encoding="utf-8").strip()
                if raw.startswith("psql "):
                    raw = raw[len("psql ") :].strip()
                return raw or None
        except OSError:
            # Ignore and fall back to env.
            continue
    return None


@dataclass(frozen=True)
class Settings:
    """Strongly-typed runtime settings loaded from environment variables."""

    # App
    app_name: str = "Resident Directory API"
    app_version: str = "0.1.0"

    # Networking / CORS
    allow_origins: tuple[str, ...] = ("http://localhost:3000",)

    # Database
    database_url: str = ""

    # Auth
    jwt_issuer: str = "resident-directory"
    jwt_audience: str = "resident-directory-frontend"
    access_token_expires_minutes: int = 30
    refresh_token_expires_days: int = 30
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"

    # Cloudinary (stub)
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    @staticmethod
    def load() -> "Settings":
        """
        Load settings from environment.

        Required env vars:
        - DATABASE_URL OR POSTGRES_URL (preferred), OR resident_db/db_connection.txt present
        - JWT_SECRET_KEY
        """
        db_url = (
            os.getenv("DATABASE_URL")
            or os.getenv("POSTGRES_URL")
            or _read_db_connection_txt()
            or ""
        )
        secret = os.getenv("JWT_SECRET_KEY", "")

        # CORS: allow comma-separated env var override if desired.
        allow_origins_env = os.getenv("ALLOW_ORIGINS", "")
        allow_origins = ("http://localhost:3000",)
        if allow_origins_env.strip():
            allow_origins = tuple([o.strip() for o in allow_origins_env.split(",") if o.strip()])

        return Settings(
            app_name=os.getenv("APP_NAME", "Resident Directory API"),
            app_version=os.getenv("APP_VERSION", "0.1.0"),
            allow_origins=allow_origins,
            database_url=db_url,
            jwt_issuer=os.getenv("JWT_ISSUER", "resident-directory"),
            jwt_audience=os.getenv("JWT_AUDIENCE", "resident-directory-frontend"),
            access_token_expires_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", "30")),
            refresh_token_expires_days=int(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", "30")),
            jwt_secret_key=secret,
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            cloudinary_cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
            cloudinary_api_key=os.getenv("CLOUDINARY_API_KEY", ""),
            cloudinary_api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
        )


settings = Settings.load()
