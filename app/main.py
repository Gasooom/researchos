"""Application entry point for ResearchOS."""

from app.core.config import get_settings


def main() -> None:
    """Start the ResearchOS application."""
    settings = get_settings()

    print(
        f"ResearchOS is starting in {settings.app_env} "
        f"mode with {settings.log_level} logging."
    )


if __name__ == "__main__":
    main()
