import logging
from tqdm import tqdm


class TqdmLoggingHandler(logging.Handler):

    def emit(self, record):

        try:
            msg = self.format(record)
            tqdm.write(msg)
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