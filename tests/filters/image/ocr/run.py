import logging
from typing import Any
import sys
import os
import re

import easyocr
import fasttext

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
logger.info(logging.INFO)


class OCRFilter(Filter):
    """Implementation of OCR."""

    LANGUAGES = {"eng": "en", "rus": "ru"}

    ML_MODELS_CONFIG = {
        "easyocr": {
            "dirname": "models/image/ocr",
            "filenames": ["craft_mlt_25k.pth", "cyrillic_g2.pth"],
            "urls": ["", ""],
        },
        "language_recognition": {
            "repo_id": "facebook/fasttext-language-identification",
            "dirname": "models/image/language_recognition",
            "filenames": ["model.bin"],
            "urls": ["", ""],
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        path = os.path.join(
            self.current_path,
            self.ML_MODELS_CONFIG["language_recognition"]["dirname"],
            self.ML_MODELS_CONFIG["language_recognition"]["filenames"][0],
        )

        self.language_model = fasttext.load_model(path)

        self.easyocr_reader = easyocr.Reader(
            [*self.LANGUAGES.values()],
            model_storage_directory=os.path.join(
                self.current_path, self.ML_MODELS_CONFIG.get("easyocr").get("dirname")
            ),
            download_enabled=False,
        )

    def __recognize_language_for_word(self, word: str) -> str:
        """
        Apply ML model to recognize language of specified word.
        Parameters
        ----------
        word

        Returns
        -------

        """

        pattern = r"(\w+)_"
        language = self.language_model.predict(word.lower())[0][0]
        language = re.search(pattern, language.replace("__label__", ""))
        return language.group(1)

    def __recognize_language_for_words(self, words_list: list[str]) -> list[str]:
        """
        Apply ML model to recognize language of specified words list.
        Parameters
        ----------
        words_list
        List of str words
        Returns
        -------

        """
        return [self.__recognize_language_for_word(word) for word in words_list]

    def apply_for_file(self, context_data: dict[str:Any]) -> dict[str, Any]:
        """
        Apply OCR filter to one file
        Parameters
        ----------
        sample_path
        Path to file on the local file system.
        context_data
        context data example: path, label ..
        Returns
        -------

        """
        sample_path = context_data["path"]
        if os.path.exists(sample_path):
            try:
                result = self.easyocr_reader.readtext(sample_path)
                result = list(map(lambda x: x[:2], result))

                box_list = [line[0] for line in result]
                text_list = [line[1] for line in result]

                languages_list = self.__recognize_language_for_words(text_list)
                return {
                    "path": sample_path,
                    "box_list": box_list,
                    "approx_text_list": text_list,
                    "approx_languages_list": languages_list,
                }
            except Exception:
                return {
                    "path": sample_path,
                    "box_list": [],
                    "approx_text_list": [],
                    "approx_languages_list": [],
                }


if __name__ == "__main__":
    runner: RunnerFilter = RunnerFilter(OCRFilter)
    runner.run()
