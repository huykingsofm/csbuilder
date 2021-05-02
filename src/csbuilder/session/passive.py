from csbuilder.session.session import Session
from csbuilder.cspacket.cspacket import CSPacket
from csbuilder.session.result import SessionResult

from hkserror import HTypeError


class PassiveSession(Session):
    def respond(
            self,
            source: str,
            packet: CSPacket,
            *args,
            **kwargs
        ) -> SessionResult:
        if not isinstance(source, str):
            raise HTypeError("des", source, str)

        if not isinstance(packet, CSPacket):
            raise HTypeError("packet", packet, CSPacket)

        state = packet.state()
        if state == self._activation and not self._is_running:
            self.begin()

        return super().respond(source, packet, *args, **kwargs)
