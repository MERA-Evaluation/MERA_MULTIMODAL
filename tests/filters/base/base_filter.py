import os
import sys
import logging

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "base")
)

from base_map import BaseMap


logger = logging.getLogger(__name__)


class Filter(BaseMap):
    """
    Base abstract class for filters.
    """

    ...

    @property
    def class_file(self) -> str:
        """
        Get the class name.
        Returns
        -------
        Class name
        """
        name = self.__class__.__name__
        name = name.replace("Filter", "").lower()
        name += self.RESULT_FORMAT
        return name
