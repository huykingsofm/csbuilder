from hks_pylib.hksenum import HKSEnum, get_enum

from csbuilder.standard import Roles, States, Protocols
from csbuilder.standard import PROTOCOL_SIZE, INT_SIZE, ROLE_SIZE, STATE_SIZE

from hkserror.hkserror import HTypeError
from csbuilder.errors.packet import PacketError, PacketExtractingError


class CSPacketField(HKSEnum):
    PROTOCOL = "protocol"
    STATE = "state"
    ROLE = "role"
    OPTION = "option"
    PAYLOAD = "payload"


class CSPacket(object):
    def __init__(
                    self,
                    protocol: Protocols = None,
                    role: Roles = None,
                    state: States = None,
                    option: bytes = b"",
                    payload: bytes = b""
                ) -> None:
        if protocol is not None and not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols, None)

        if state is not None and not isinstance(state, States):
            raise HTypeError("state", state, States, None)

        if role is not None and not isinstance(role, Roles):
            raise HTypeError("role", role, Roles, None)

        if not isinstance(option, bytes):
            raise HTypeError("option", option, bytes)

        if not isinstance(payload, bytes):
            raise HTypeError("payload", payload, bytes)

        self.__packet: dict[CSPacketField, object] = {
                CSPacketField.PROTOCOL: None,
                CSPacketField.STATE: None,
                CSPacketField.ROLE: None,
                CSPacketField.OPTION: b"",
                CSPacketField.PAYLOAD: b""
            }

        self._is_valid = False

        if protocol is not None:
            self.protocol(protocol)

        if state is not None:
            self.state(state)

        if role is not None:
            self.role(role)

        self.option(option)
        self.payload(payload)

    def __getitem__(self, index: CSPacketField) -> object:
        if not isinstance(index, CSPacketField):
            raise HTypeError("index", index, CSPacketField)

        return self.__packet[index]

    def __setitem__(self, index: CSPacketField, value: object) -> None:
        if not isinstance(index, CSPacketField):
            raise HTypeError("index", index, CSPacketField)

        if index == CSPacketField.PROTOCOL:
            self.protocol(value)
        elif index == CSPacketField.STATE:
            self.state(value)
        elif index == CSPacketField.OPTION:
            self.option(value)
        elif index == CSPacketField.PAYLOAD:
            self.payload(value)
        else:
            self.__packet.update({index: value})

    def __str__(self):
        return str(self.__packet)

    def __repr__(self) -> str:
        return str(self)

    def to_bytes(self) -> bytes:
        if self._is_valid is False:
            raise PacketError("Invalid packet, it cannot create bytes form.")

        packet = b""
        
        packet += self.__packet[CSPacketField.PROTOCOL].value.to_bytes(PROTOCOL_SIZE, "big")

        packet += self.__packet[CSPacketField.ROLE].value.to_bytes(ROLE_SIZE, "big")

        packet += self.__packet[CSPacketField.STATE].value.to_bytes(STATE_SIZE, "big")

        packet += len(self.__packet[CSPacketField.OPTION]).to_bytes(INT_SIZE, "big")
        packet += self.__packet[CSPacketField.OPTION]

        packet += self.__packet[CSPacketField.PAYLOAD]

        return packet

    @staticmethod
    def from_bytes(data: bytes):
        from csbuilder.pool import Pool

        if not isinstance(data, bytes):
            raise HTypeError("data", data, bytes)

        cursor = 0

        bprotocol = data[cursor: cursor + PROTOCOL_SIZE]
        cursor += PROTOCOL_SIZE

        brole = data[cursor: cursor + ROLE_SIZE]
        cursor += ROLE_SIZE

        bstate = data[cursor: cursor + STATE_SIZE]
        cursor += STATE_SIZE

        boptional_length = data[cursor: cursor + INT_SIZE]
        cursor += INT_SIZE

        if len(bprotocol) != PROTOCOL_SIZE:
            raise PacketExtractingError("Invalid protocol, expected {} "
            "bytes, but got {} bytes.".format(PROTOCOL_SIZE, len(bprotocol)))

        if len(brole) != ROLE_SIZE:
            raise PacketExtractingError("Invalid role, expected {} "
            "bytes, but got {} bytes.".format(ROLE_SIZE, len(brole)))

        if len(bstate) != STATE_SIZE:
            raise PacketExtractingError("Invalid state, expected {} "
            "bytes, but got {} bytes.".format(STATE_SIZE, len(bstate)))

        if len(boptional_length) != INT_SIZE:
            raise PacketExtractingError("Invalid option length, expected {} "
            "bytes, but got {} bytes.".format(INT_SIZE, len(boptional_length)))

        iprotocol = int.from_bytes(bprotocol, "big")
        protocol = Pool.int2protocol(iprotocol)
        if protocol is None:
            raise PacketExtractingError("Unknown protocol {}.".format(iprotocol))

        irole = int.from_bytes(brole, "big")
        all_roles = Pool.get_roles(protocol)
        role = get_enum(all_roles, irole, None)
        if role is None:
            raise PacketExtractingError("Unknown role {} in {}.".format(irole, protocol))

        istate = int.from_bytes(bstate, "big")
        state = Pool.get_states(protocol, role).get(istate, None)

        if state is None:
            raise PacketExtractingError("Unknown state {} in {}-{}.".
                    format(istate, protocol, role))

        option_length = int.from_bytes(boptional_length, "big")
        option = data[cursor: cursor + option_length]
        cursor += option_length

        if len(option) < option_length:
            raise PacketExtractingError("Optional header is not enough length.")

        payload = data[cursor: ]

        packet = CSPacket(protocol, role, state, option, payload)

        return packet

    def _validate(self):
        from csbuilder.pool import Pool
        protocol = self.protocol()
        role = self.role()
        state = self.state()

        if not protocol or not role or not state:
            return

        states = Pool.get_states(protocol, role)
        if state not in states:
            raise PacketError("Packet is invalid "
            "because mismatched elements ({}, {}, {})".format(protocol, role, state))

        self._is_valid = True

    def protocol(self, protocol: Protocols = None) -> Protocols:
        if protocol == None:
            return self.__packet[CSPacketField.PROTOCOL]

        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols, None)

        self._is_valid = False

        self.__packet[CSPacketField.PROTOCOL] = protocol

        self._validate()

    def role(self, role: Roles = None) -> Roles:
        if role == None:
            return self.__packet[CSPacketField.ROLE]

        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles, None)

        self._is_valid = False

        self.__packet[CSPacketField.ROLE] = role

        self._validate()

    def state(self, state: States = None) -> States:
        if state == None:
            return self.__packet[CSPacketField.STATE]

        if not isinstance(state, States):
            raise HTypeError("state", state, States, None)

        self._is_valid = False

        self.__packet[CSPacketField.STATE] = state

        self._validate()

    def option(self, option: bytes = None) -> bytes:
        if option == None:
            return self.__packet[CSPacketField.OPTION]

        if not isinstance(option, bytes):
            raise HTypeError("option", option, bytes, None)

        self.__packet[CSPacketField.OPTION] = option

    def update_option(self, option: bytes) -> None:
        if not isinstance(option, bytes):
            raise HTypeError("option", option, bytes)

        self.__packet[CSPacketField.OPTION] += option

    def payload(self, payload: bytes = None) -> bytes:
        if payload is None:
            return self.__packet[CSPacketField.PAYLOAD]

        if not isinstance(payload, bytes):
            raise HTypeError("payload", payload, bytes, None)

        self.__packet[CSPacketField.PAYLOAD] = payload

    def update_payload(self, payload: bytes):
        if not isinstance(payload, bytes):
            raise HTypeError("payload", payload, bytes)

        self.__packet[CSPacketField.PAYLOAD] += payload
