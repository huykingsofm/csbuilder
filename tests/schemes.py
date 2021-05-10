import csbuilder
from csbuilder.standard import Protocols, Roles


@csbuilder.protocols
class MyProtocols(Protocols):
    SUBMIT = 1
    CONTROL = 2


@csbuilder.roles(protocol=MyProtocols.SUBMIT)
class SubmitRoles(Roles):
    SERVER = 0
    CLIENT = 1


@csbuilder.roles(protocol=MyProtocols.CONTROL)
class ControlRoles(Roles):
    DRIVER = 0
    DEVICE = 1
