import logging
import os


def setup_logging(agent_name: str) -> logging.Logger:
    """Uniform logging across all agents — respects LOG_LEVEL env var, defaults to INFO."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format=f"%(asctime)s [{agent_name}] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger(agent_name)
