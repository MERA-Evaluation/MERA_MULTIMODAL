import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mera"))

from mera_checkouts import BaseMeraCheckout
from common_checkouts.common_checkout import CommonCheckout

MERA_CHECKOUTS = BaseMeraCheckout.__subclasses__()
COMMON_CHECKOUTS = set(CommonCheckout.__subclasses__() + MERA_CHECKOUTS)

PROJECTS_CONFIGS = {"mera": MERA_CHECKOUTS, "common": COMMON_CHECKOUTS}
