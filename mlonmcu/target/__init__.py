"""MLonMCU target submodule"""

# from .target import Target
#
# SUPPORTED_TARGETS = {
#     "etiss/pulpino": Target("etiss/pulpino"),
#     "host": Target("host"),
# }  # TODO

from .etiss_pulpino import ETISSPulpinoTarget
from .host_x86 import HostX86Target

SUPPORTED_TARGETS = {
    "etiss_pulpino": ETISSPulpinoTarget,
    "host_x86": HostX86Target,
}
