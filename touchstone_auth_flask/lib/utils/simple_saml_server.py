"""touchstone_auth_flask/lib/utils/simple_saml_server.py

This module provides the ability to run a SimpleSAMLPHP server locally via Docker.
"""

# ruff: noqa: ANN401

import logging
import os
import signal
import sys
from typing import Any

import docker
from docker.models.containers import Container

logger = logging.getLogger(__name__)
logging.basicConfig(level="INFO")
logger.setLevel("INFO")

container: Container | None = None


def stop_container(_signal: Any, _frame: Any) -> None:
    global container  # noqa: PLW0602
    message = f"Stopping container: {container}"
    logger.info(message)
    if container is not None:
        container.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, stop_container)


def run_simple_saml_server() -> None:
    client = docker.from_env()
    global container  # noqa: PLW0603
    container = client.containers.run(
        "kenchan0130/simplesamlphp",
        detach=True,
        environment={
            "SIMPLESAMLPHP_SP_ENTITY_ID": os.environ["SP_ENTITY_ID"],
            "SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE": os.environ["SP_ACS_URL"],
        },
        ports={"8080": "8080"},
    )
    for log_line in container.logs(stream=True, stdout=True, stderr=True):
        logger.info(log_line.decode().strip())


if __name__ == "__main__":
    run_simple_saml_server()
