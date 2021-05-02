import csbuilder
from csbuilder.standard import States

from tests.schemes import ControlRoles, MyProtocols


@csbuilder.states(protocol=MyProtocols.CONTROL, role=ControlRoles.DRIVER)
class ControlDriverStatusGroup(States):
    IGNORE = 0
    REQUEST = 1


@csbuilder.states(protocol=MyProtocols.CONTROL, role=ControlRoles.DEVICE)
class ControlDeviceStatusGroup(States):
    IGNORE = 0
    ACCEPT = 1
    DENY = 2
