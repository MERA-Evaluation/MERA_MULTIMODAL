import os
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "base")
)

from base_checkout import BaseCheckout


class CommonCheckout(BaseCheckout): ...
