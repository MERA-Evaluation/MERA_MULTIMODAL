import logging
import json
import traceback
import ast


class ELKFormatter(logging.Formatter):
    """Формат логирования для ELK."""

    MOSCOW_TIMEZONE_FORMAT = "%Y-%m-%d %H:%M:%S %Z%z"

    @staticmethod
    def get_error_params(record) -> tuple[str, str, str, str]:
        """
        Распарсить информацию из лога с уровнем ERROR.
        """

        user_error_message = record.getMessage()
        if hasattr(record, "exc_info"):
            exc_type, exc_value, exc_traceback = record.exc_info
            if exc_type:
                error_class = exc_type.__name__
                error_message = str(exc_value)
                record.msg = f"{error_class}: {error_message}"

                traceback_str = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )

                return error_message, user_error_message, error_class, traceback_str

    def format(self, record):
        record.asctime = self.formatTime(record, self.MOSCOW_TIMEZONE_FORMAT)

        if record.levelno not in (logging.ERROR, logging.CRITICAL):
            message = record.getMessage()
            try:
                dict_message = ast.literal_eval(message)
                message = {key + "_depp": value for key, value in dict_message.items()}
            except:
                message = record.getMessage()
            log_dict = {
                "level_depp": record.levelname,
                "timestamp_depp": record.asctime,
                "message_depp": message,
                "filename_depp": record.filename,
                "lineno_depp": record.lineno,
                "funcName_depp": record.funcName,
                "module_depp": record.module,
            }
            return json.dumps(log_dict)
        (error_default_message, error_user_message, error_type, trb) = (
            self.get_error_params(record)
        )
        log_dict = {
            "level_depp": record.levelname,
            "timestamp_depp": record.asctime,
            "message_depp": {
                "error_default_message_depp": error_default_message,
                "error_user_message_depp": error_user_message,
                "error_type_depp": str(error_type),
                "traceback_depp": str(trb),
            },
            "filename_depp": record.filename,
            "lineno_depp": record.lineno,
            "funcName_depp": record.funcName,
            "module_depp": record.module,
        }
        return json.dumps(log_dict)
