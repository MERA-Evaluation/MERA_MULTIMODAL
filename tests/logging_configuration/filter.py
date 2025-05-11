import logging

EXCLUDE_FILE_LOGGING = [
    "connectionpool.py",
]


class ExcludeFileFilter(logging.Filter):
    def filter(self, record):
        return record.filename not in EXCLUDE_FILE_LOGGING
