from csbuilder.errors import CSError

class PacketError(CSError):
    "The exception is raised by failures in Packet."


class PacketExtractingError(PacketError):
    "The exception is raised by failures in packet extracting."
