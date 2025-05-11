import logging
import ssl
import time
from urllib.error import URLError

import requests
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # pylint: disable=E0401
from requests.packages.urllib3.exceptions import InsecureRequestWarning

logger = logging.getLogger(__name__)


def retry_decorator(sleep_period=None, retries=None):
    if sleep_period is None or retries is None:
        raise Exception("Please, set up all params in retry decorator.")

    def func_wrapper(func):
        def params_wrapper(*args, **kwargs):
            retries_cntr = retries
            while retries_cntr > 0:
                try:
                    return func(*args, **kwargs)
                except (
                    ssl.SSLError,
                    URLError,
                    ValueError,
                    urllib3.exceptions.SSLError,
                    TypeError,
                    requests.exceptions.SSLError,
                    urllib3.exceptions.ProtocolError,
                    requests.exceptions.ConnectionError,
                ):
                    logger.error(f"FAIL FOR args={args}, kwargs={kwargs}")
                    time.sleep(sleep_period)
                    retries_cntr -= 1
                    logger.info("RETRYES LEFT: ", retries_cntr)

                except Exception as ex:
                    logger.error(f"FAIL FOR args={args}, kwargs={kwargs}")
                    raise ex
            raise requests.HTTPError("Max exception retries exceeded in wrapper.")

        return params_wrapper

    return func_wrapper


class HttpWrapper:
    def __init__(self, total_retries=12, backoff_factor=2):
        """
        :param total_retries: number of retries
        :param backoff_factor: upscale factor for next try timeout
        """
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        retry_strategy = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504, 495, 496, 526],
            method_whitelist=["HEAD", "GET", "POST", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        self.http = requests.Session()
        self.http.mount("https://", adapter)
        self.http.mount("http://", adapter)

    @retry_decorator(sleep_period=10, retries=25)
    def get(self, *args, **kwargs):
        return self.http.get(*args, **kwargs)

    @retry_decorator(sleep_period=5, retries=25)
    def post(self, *args, **kwargs):
        return self.http.post(*args, **kwargs)

    @retry_decorator(sleep_period=5, retries=25)
    def request(self, *args, **kwargs):
        return self.http.request(*args, **kwargs)

    @retry_decorator(sleep_period=5, retries=25)
    def head(self, *args, **kwargs):
        return self.http.head(*args, **kwargs)


http = HttpWrapper()
