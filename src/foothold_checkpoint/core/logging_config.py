"""File logging setup for the foothold-checkpoint tool.

The library itself never configures logging: every module just asks for a logger
and writes to it. Attaching handlers is the application's job, which keeps two
very different hosts happy.

- The CLI calls :func:`setup_file_logging` so that operations leave a trace on
  disk, which is what lets an operator explain after the fact why a restore
  behaved the way it did.
- The DCSServerBot plugin calls nothing. The bot owns the logging configuration,
  and records emitted here propagate up to it.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

#: Root logger name for the package. Everything the tool logs lives under it.
PACKAGE_LOGGER_NAME = "foothold_checkpoint"

#: Where the CLI writes its log when the caller does not pick a path.
DEFAULT_LOG_FILE = Path.home() / ".foothold-checkpoint" / "logs" / "foothold-checkpoint.log"

#: Rotate at 5 MB and keep three older files, so a runaway loop cannot fill a disk.
MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

#: Marks the handler this module installs, so repeated calls replace it instead
#: of stacking duplicates and writing every record several times.
_HANDLER_TAG = "foothold-checkpoint-file-handler"


def get_logger(name: str) -> logging.Logger:
    """Return a logger without configuring anything.

    Args:
        name: Dotted logger name, conventionally the module's ``__name__``.

    Returns:
        The requested logger.

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("checkpoint restored")
    """
    return logging.getLogger(name)


def setup_file_logging(
    log_file: str | Path | None = None,
    level: int = logging.INFO,
) -> Path | None:
    """Send package log records to a rotating file.

    Safe to call more than once: a previously installed handler is replaced
    rather than added to.

    Args:
        log_file: Destination file. Defaults to :data:`DEFAULT_LOG_FILE`.
        level: Lowest level to record. Defaults to ``logging.INFO``; pass
            ``logging.DEBUG`` for verbose diagnostics.

    Returns:
        The log file in use, or ``None`` when it could not be opened. Logging to
        a file is a convenience, never a reason to fail the user's command.

    Examples:
        >>> setup_file_logging()  # doctest: +SKIP
        PosixPath('/home/user/.foothold-checkpoint/logs/foothold-checkpoint.log')
        >>> setup_file_logging("C:/temp/debug.log", level=logging.DEBUG)  # doctest: +SKIP
        WindowsPath('C:/temp/debug.log')
    """
    log_path = Path(log_file) if log_file is not None else DEFAULT_LOG_FILE

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    # Build the replacement before discarding what works: a reconfiguration that
    # fails must leave logging exactly as it was, not silently switch it off.
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
    except OSError:
        # An unusable log path must never take the command down with it.
        return None

    handler.set_name(_HANDLER_TAG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    handler.setLevel(level)

    _remove_existing_handler(package_logger)
    package_logger.addHandler(handler)

    # Only lower the logger's own threshold, never raise it above what a host
    # application (the Discord bot) may have already chosen.
    if package_logger.level == logging.NOTSET or package_logger.level > level:
        package_logger.setLevel(level)

    return log_path


def _remove_existing_handler(logger: logging.Logger) -> None:
    """Detach and close a handler previously installed by this module.

    Args:
        logger: Logger to clean up.
    """
    for handler in logger.handlers[:]:
        if handler.get_name() == _HANDLER_TAG:
            logger.removeHandler(handler)
            handler.close()
