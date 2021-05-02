from hks_pylib.done import Done
from hkserror.hkserror import HTypeError

from csbuilder.cspacket.cspacket import CSPacket


class SchemeResult(object):
    def __init__(
                self,
                destination: str,
                packet: CSPacket,
                is_continue: bool,
                result:Done = Done(None)
            ) -> None:
        if destination is not None and not isinstance(destination, str):
            raise HTypeError("destination", destination, str)
        
        if packet is not None and not isinstance(packet, CSPacket):
            raise HTypeError("packet", packet, CSPacket, None)

        if not isinstance(is_continue, bool):
            raise HTypeError("is_continue", is_continue, bool)

        if not isinstance(result, Done):
            raise HTypeError("result", result, Done)

        self.destination = destination
        self.packet = packet
        self.is_continue = is_continue
        self.result = result
