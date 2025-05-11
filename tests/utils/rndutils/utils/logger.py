import logging


def get_logger(name: str = "default", verbose: bool = False):
    logging.basicConfig(
        format="[LINE:%(lineno)d] %(levelname)-8s [%(asctime)s]  %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )
    logger = logging.getLogger(name)
    return logger
