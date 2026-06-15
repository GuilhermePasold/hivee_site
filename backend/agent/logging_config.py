import logging
import sys

logger = logging.getLogger(__name__)


def setup_logging():
    agent_logger = logging.getLogger("agent")
    agent_logger.setLevel(logging.DEBUG)

    if any(isinstance(handler, logging.StreamHandler) for handler in agent_logger.handlers):
        return agent_logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s.%(funcName)s:%(lineno)d  %(levelname)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    agent_logger.addHandler(handler)
    return agent_logger
