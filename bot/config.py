"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os

class ConfigurationError(RuntimeError):
    """Raised when required application configuration is missing."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    api_secret: str

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            from dotenv import load_dotenv
        except ImportError as exc:
            raise ConfigurationError(
                "python-dotenv is not installed. Run: pip install -r requirements.txt"
            ) from exc

        load_dotenv()
        api_key = os.getenv("BINANCE_API_KEY", "").strip()
        api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

        missing = []
        if not api_key:
            missing.append("BINANCE_API_KEY")
        if not api_secret:
            missing.append("BINANCE_API_SECRET")

        if missing:
            raise ConfigurationError(
                f"Missing required environment variable(s): {', '.join(missing)}"
            )

        return cls(api_key=api_key, api_secret=api_secret)
