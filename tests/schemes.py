import csbuilder
from csbuilder.standard import StandardRole, Protocols, Roles


@csbuilder.protocols
class MyProtocols(Protocols):
    SUBMIT = 1
    CONTROL = 2


@csbuilder.roles(protocol=MyProtocols.SUBMIT)
class SubmitRoles(Roles):
    SERVER = StandardRole.PASSIVE
    CLIENT = StandardRole.ACTIVE


@csbuilder.roles(protocol=MyProtocols.CONTROL)
class ControlRoles(Roles):
    DRIVER = StandardRole.ACTIVE
    DEVICE = StandardRole.PASSIVE
