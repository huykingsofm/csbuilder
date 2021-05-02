from typing import Tuple

from hks_pylib.done import Done

from csbuilder.standard import States
from csbuilder.scheme.result import SchemeResult
from csbuilder.cspacket.cspacket import CSPacket

from hkserror.hkserror import HTypeError
from csbuilder.errors import ManagementScopeError


class Scheme(object):
    def __init__(self) -> None:
        from csbuilder.pool import Pool

        self._protocol, self._role = Pool.revert_scheme(type(self))
        self._states = Pool.get_states(self._protocol, self._role)

        self._is_running = False

        self._ignore_packet = CSPacket(
                self._protocol,
                self._states.IGNORE
            )

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

    def __sample_states(
            self,
            source: str,
            packet: CSPacket,
            *args,
            **kwargs
        ) -> Tuple[str, CSPacket, bool, Done]:
        packet = CSPacket(self._scheme, self._states.REQUEST)
        destination = "Forwarder"  # Destination of packet
        cont = True  # Continue scheme
        result = Done(False)  # result of the scheme 
                        # (result is normally None, but if cont = False,
                        # result can be set to not-None value)
        return destination, packet.create(), cont, result

    def generate_packet(self, state: States, option: bytes = b"", payload: bytes = b""):
        if not isinstance(state, States):
            raise HTypeError("state", state, States)
        
        if state not in self._states:
            raise ManagementScopeError("The state {} doesn't belong "
            "to {}".format(state, self._states))

        return CSPacket(
                protocol=self._protocol,
                state=state,
                option=option,
                payload=payload
            )

    def ignore(self, source: str) -> SchemeResult:
        return SchemeResult(
                source,
                self._ignore_packet,
                False,
                Done(False, reason = "Invalid packet")
            )
