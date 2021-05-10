from typing import Tuple

from hks_pylib.done import Done

from csbuilder.standard import States
from csbuilder.scheme.result import SchemeResult
from csbuilder.cspacket.cspacket import CSPacket

from hkserror.hkserror import HFormatError, HTypeError
from csbuilder.errors import ManagementScopeError


class Scheme(object):
    def __init__(self) -> None:
        from csbuilder.pool import Pool

        self._protocol, self._role = Pool.revert_scheme(type(self))
        self._states = Pool.get_states(self._protocol, self._role)

        self._is_running = False

    def protocol(self):
        return self._protocol
    
    def role(self):
        return self._role

    def is_running(self):
        return self._is_running

    def begin(self, *args, **kwargs) -> None:
        self._is_running = True

    def cancel(self, *args, **kwargs) -> None:
        self._is_running = False

    def generate_packet(self, state: States, option: bytes = b"", payload: bytes = b""):
        if not isinstance(state, States):
            raise HTypeError("state", state, States)
        
        if state not in self._states:
            raise ManagementScopeError("The state {} doesn't belong "
            "to {}".format(state, self._states))

        return CSPacket(
                protocol=self._protocol,
                role=self._role,
                state=state,
                option=option,
                payload=payload
            )

    def ignore(self, source: str, reason: str = "Invalid packet") -> SchemeResult:
        if not isinstance(reason, str):
            raise HTypeError("reason", reason, str)

        packet = self.generate_packet(self._states.IGNORE)
        packet.payload(reason.encode())

        return SchemeResult(source, packet, False, Done(False, reason=reason))

    def config(self, **kwargs):
        if kwargs:
            raise HFormatError("Unexpected parameters ({})".format(set(kwargs.keys())))
