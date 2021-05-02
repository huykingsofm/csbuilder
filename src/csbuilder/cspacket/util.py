from hks_pylib.done import Done
from hkserror.hkserror import HTypeError

from csbuilder.cspacket.cspacket import CSPacket, CSPacketField
from csbuilder.standard import Protocols, Roles, States, INT_SIZE

from csbuilder.errors.packet import PacketExtractingError


class CSPacketUtil(object):
    @staticmethod
    def get_protocol(data: bytes):
        from csbuilder.pool import Pool
        
        if not isinstance(data, bytes):
            raise HTypeError("data", data, bytes)

        bprotocol = data[0: INT_SIZE]
        if len(bprotocol) == 0:
            raise PacketExtractingError("Scheme is not provided.")
        
        iprotocol = int.from_bytes(bprotocol, "big")

        protocol = Pool.int2protocol(iprotocol)

        if protocol is None:
            raise PacketExtractingError("Unknown protocol {}.".format(iprotocol))

        return protocol

    @staticmethod
    def extract(data: bytes, role: Roles) -> CSPacket:
        from csbuilder.pool import Pool
        
        if not isinstance(data, bytes):
            raise HTypeError("data", data, bytes)

        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        bprotocol = data[0: INT_SIZE]
        bstate = data[INT_SIZE: 2 * INT_SIZE]
        boptional_length = data[2 * INT_SIZE: 3 * INT_SIZE]

        if len(bprotocol) == 0:
            raise PacketExtractingError("Scheme is not provided.")

        if len(bstate) == 0:
            raise PacketExtractingError("Status is not provided.")

        if len(boptional_length) == 0:
            raise PacketExtractingError("Optional length is not provided.")

        iprotocol = int.from_bytes(bprotocol, "big")
        protocol = Pool.int2protocol(iprotocol)
        if protocol is None:
            raise PacketExtractingError("Unknown protocol {}.".format(iprotocol))

        istate = int.from_bytes(bstate, "big")
        state = Pool.get_states(protocol, role).get(istate, None)

        if state is None:
            raise PacketExtractingError("Unknown state {} in protocol {}.".
                    format(istate, protocol.name))

        option_length = int.from_bytes(boptional_length, "big")
        option = data[3 * INT_SIZE: 3 * INT_SIZE + option_length]

        if len(option) < option_length:
            raise PacketExtractingError("Optional header is not enough length.")

        payload = data[3 * INT_SIZE + option_length: ]

        packet = CSPacket(protocol, state, option, payload)
        
        return packet

    @staticmethod
    def check(
            data: object,
            expected_protocol: Protocols,
            expected_state: States,
            role: Roles,
            is_packet: bool = False
        ) -> Done:
        if not isinstance(data, bytes) and not isinstance(data, CSPacket):
            raise HTypeError("data", data, bytes, CSPacket)

        if not isinstance(expected_protocol, Protocols):
            raise HTypeError("expected_protocol", expected_protocol, Protocols)

        if not isinstance(expected_state, States):
            raise HTypeError("expected_state", expected_state, States)

        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        packet: CSPacket = None
        if is_packet:
            packet = data
        else:
            packet = CSPacketUtil.extract(data, role)

        if packet.protocol() != expected_protocol:
            return Done(False,
                        field=CSPacketField.PROTOCOL,
                        actual=packet.protocol().name,
                        expected=expected_protocol.name
                    )

        if packet.state() != expected_state:
            return Done(False,
                        field=CSPacketField.STATE,
                        actual=packet.state().name,
                        expected=expected_state.name
                    )

        return Done(True)
