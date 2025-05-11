import logging

logger = logging.getLogger(__name__)


class Runnable:
    def _command(self, command, **kwargs):
        param_str = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.debug(f"{command}: {param_str}")
        try:
            func = getattr(self, command)
        except AttributeError:
            raise NotImplementedError(command)
        return func

    def run_command(self, command, **kwargs):
        """This wrapper attempts to fill all keyword arguments in command
        with data from kwargs and runs the command

        :param command: command to run
        :param kwargs: arguments dict to search keyword args in
        """
        func = self._command(command, **kwargs)

        params = {}
        for n, item in enumerate(func.__code__.co_varnames):
            if item == "self":
                continue
            if n >= func.__code__.co_argcount:
                break
            if item in kwargs:
                params[item] = kwargs.get(item)
        return func(**params)

    def run_extended_command(self, command, **kwargs):
        func = self._command(command, **kwargs)

        params = {}
        for k, v in kwargs.items():
            params[k] = v
        return func(**params)
