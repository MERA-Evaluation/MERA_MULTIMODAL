import logging
from typing import Any, Generator

from .base_extractor import BaseExtractor


logger = logging.getLogger(__name__)


class PrefixExtractor(BaseExtractor):
    def __init__(self, client, root_folder: str):
        super().__init__(client)
        self.root_folder = root_folder

    def extract(self) -> Generator[dict[str, Any], None, None]:
        """
        Create a generator object extracting
        {
          "path": <path_value>,
          <metric_field_1>: <metric_field_1_value>,
          <metric_field_2>: <metric_field_2_value>,
          ...
        }
        dictionaries from source storage.
        Returns
        --------
        Generator object
        """
        client_data = self.client.get_all_files()
        client_data = self.client.process_client_data(client_data)
        for batch_data in client_data:
            batch = self.format_depp_map_output(path=batch_data)
            yield batch
