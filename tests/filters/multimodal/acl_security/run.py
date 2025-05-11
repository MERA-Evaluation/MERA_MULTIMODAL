import os
import sys
from typing import Any
import logging


base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.extend(
    [
        os.path.join(base_dir, "utils"),
        os.path.join(base_dir, "base"),
        os.path.join(os.path.dirname(base_dir), "logging_configuration"),
    ]
)

from runner_filter import RunnerFilter
from base_filter import Filter
from configure_logging import configure_logger


configure_logger()
logger = logging.getLogger(__name__)


class ACLSecurityFilter(Filter):
    def create_s3_key(self, file_path: str) -> str:
        s3_key = "/".join(file_path.split("/")[1:])
        return s3_key

    def apply_for_file(self, context_data: dict[str, Any]) -> dict[str, Any]:
        return context_data

    def apply_for_files(
        self, batch_context_data: list[dict[str, Any]], **kwargs
    ) -> list[dict[str, Any]]:
        client = self.map_kwargs.get("client")
        if "check_all_files_acl" in dir(client):
            s3_remote_files = []
            s3_keys = []
            sample_paths = list(
                map(
                    lambda sample_context_data: sample_context_data["path"],
                    batch_context_data,
                )
            )
            for sample_context_data in batch_context_data:
                sample_path = sample_context_data["path"]
                s3_key = self.create_s3_key(sample_path)
                s3_remote_files.append(s3_key)
                s3_keys.append(s3_key)

            result = client.check_all_files_acl(s3_remote_files)
            result = [
                {"path": sample_path, "acl_security": predict}
                for sample_path, predict in zip(sample_paths, result)
            ]
            return result
        raise NotImplementedError(
            "ACL security filter is not available for this pagination type"
        )


if __name__ == "__main__":
    runner = RunnerFilter(ACLSecurityFilter)
    runner.run()
