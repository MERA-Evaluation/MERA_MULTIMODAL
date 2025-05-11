import logging

from filter import ExcludeFileFilter
from formatters import ELKFormatter


def configure_logger():
    """
    Создать объект logger с нужной конфигурацией.
    """
    formatter = ELKFormatter()
    exclude_filter = ExcludeFileFilter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(exclude_filter)
    logging.basicConfig(level=logging.INFO, handlers=(handler,))
