from hkserror import HTypeError

from csbuilder.cspacket import CSPacket


class SessionResult(object):
    def __init__(self, destination: str, packet: CSPacket) -> None:
        if destination is not None and not isinstance(destination, str):
            raise HTypeError("des", destination, str, None)

        if packet is not None and not isinstance(packet, CSPacket):
            raise HTypeError("packet", packet, CSPacket, None)

        self.destination = destination
        self.packet = packet
