import logging
import inspect
from typing import Any


logger = logging.getLogger(__name__)


def call_with_params_inspection(callable_obj, params: dict[str, Any]):
    """"""
    try:
        func_parameters = {}
        pagination_func_parameters_must = inspect.signature(callable_obj).parameters
        for params, value in params.items():
            if pagination_func_parameters_must.get(params):
                func_parameters[params] = value
        return callable_obj(**func_parameters)
    except KeyError as e:
        logger.error(
            "Wrong key",
        )
        raise e
    except TypeError as e:
        logger.error("Are not enough arguments for object %s", callable_obj)
        raise e
