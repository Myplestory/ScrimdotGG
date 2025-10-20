Client Backend API
==================

See also:
- functions.md (per-file function reference)
- matchpage.md (constructor and join flows)

.. rubric:: App Factory

- create_app() -> Quart

.. rubric:: Sockets

- on(event: str)
- get_handler(event: str) -> Handler | None

.. rubric:: Logging

- get_logger(name: str, level: int = logging.INFO) -> logging.Logger
- setup_root_logger()
