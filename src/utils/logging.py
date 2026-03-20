import logging


class TqdmLoggingHandler(logging.Handler):
    _tqdm_write = None

    @classmethod
    def _write(cls, msg: str) -> None:
        if cls._tqdm_write is None:
            from tqdm import tqdm
            cls._tqdm_write = tqdm.write
        cls._tqdm_write(msg)

    def emit(self, record):
        try:
            msg = self.format(record)
            self._write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = TqdmLoggingHandler()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        handler.setFormatter(formatter)

        logger.addHandler(handler)

        logger.setLevel(logging.INFO)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

        logger.propagate = False

    return logger