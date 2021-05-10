from hks_pylib.hksenum import HKSEnum

from csbuilder.util import LimitedInt, INT_SIZE


PROTOCOL_SIZE = 4
STATE_SIZE = 2
ROLE_SIZE = 1


class ProtocolInt(LimitedInt):
    ...


ProtocolInt.config(size=PROTOCOL_SIZE)


class StateInt(LimitedInt):
    ...


StateInt.config(size=STATE_SIZE)


class RoleInt(LimitedInt):
    ...


RoleInt.config(low=0, high=1)


class Protocols(ProtocolInt, HKSEnum):
    ...


class States(StateInt, HKSEnum):
    ...


class Roles(RoleInt, HKSEnum):
    ...
