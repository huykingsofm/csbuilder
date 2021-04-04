from csbuilder.const_group import ConstGroup
from csbuilder.packet import Packet, PacketGenerator


class Scheme(object):
    def __init__(
                    self,
                    scheme_type: int,
                    outcoming_status_group: ConstGroup,
                    incoming_status_group: ConstGroup,
                    **kwargs
                ) -> None:
        assert isinstance(scheme_type, int)
        assert isinstance(outcoming_status_group, ConstGroup)
        assert isinstance(incoming_status_group, ConstGroup)
        
        super().__init__()
        self._scheme_type = scheme_type
        self._outcoming_status_group = outcoming_status_group
        self._incoming_status_group = incoming_status_group

        self._in_process = False
        self._forwarder_name = None
        self._local_name = None
        
        self._packet_generator = PacketGenerator(self._scheme_type, self._outcoming_status_group)
        self._reset_packet = self._packet_generator.generate(self._outcoming_status_group.RESET)

    @property
    def in_process(self):
        return self._in_process

    def _sample_status(self, packet_dict, source, *args):
        packet = Packet(self._scheme_type, self._outcoming_status_group.REQUEST)
        destination = "Forwarder"  # Destination of packet
        cont = True  # Continue scheme
        return packet.create(), destination, cont

    def __assign__(self, session):
        # Assign each processing method of all status to the session
        # Processing method must return a tuple of three items (packet: bytes, des: str, cont: bool)
        # assign()
        # assign_initial()
        # assign_reset_packet()
        raise NotImplementedError("You must implement the method __assign__ before starting session")

