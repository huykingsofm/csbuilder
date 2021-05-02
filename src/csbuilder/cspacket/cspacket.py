from hks_pylib.hksenum import HKSEnum

from csbuilder.standard import Roles, States, Protocols, INT_SIZE

from hkserror.hkserror import HTypeError
from csbuilder.errors.pool import PoolError
from csbuilder.errors.packet import PacketError


class CSPacketField(HKSEnum):
    PROTOCOL = "protocol"
    STATE = "state"
    OPTION = "option"
    PAYLOAD = "payload"


class CSPacket(object):
    def __init__(
                    self,
                    protocol: Protocols = None,
                    state: States = None,
                    option: bytes = b"",
                    payload: bytes = b""
                ) -> None:
        if protocol is not None and not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols, None)

        if state is not None and not isinstance(state, States):
            raise HTypeError("state", state, States, None)

        if not isinstance(option, bytes):
            raise HTypeError("option", option, bytes)

        if not isinstance(payload, bytes):
            raise HTypeError("payload", payload, bytes)

        self._role: Roles = None

        self._packet: dict[CSPacketField, object] = {
                CSPacketField.PROTOCOL: None,
                CSPacketField.STATE: None,
                CSPacketField.OPTION: b"",
                CSPacketField.PAYLOAD: b""
            }

        if protocol is not None:
            self.protocol(protocol)
        
        if state is not None:
            self.state(state)

        self.option(option)
        self.payload(payload)

    def __getitem__(self, index: CSPacketField) -> object:
        if not isinstance(index, CSPacketField):
            raise HTypeError("index", index, CSPacketField)

        return self._packet[index]

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
            self._packet.update({index: value})

    def __str__(self):
        return str(self._packet)

    def __repr__(self) -> str:
        return str(self)

    def to_bytes(self) -> bytes:
        if not isinstance(self._packet[CSPacketField.PROTOCOL], Protocols):
            raise PacketError("Protocol is "
            "invalid {}.".format(self._packet[CSPacketField.PROTOCOL]))

        if not isinstance(self._packet[CSPacketField.STATE], States):
            raise PacketError("State is "
            "invalid {}.".format(self._packet[CSPacketField.STATE]))

        if not isinstance(self._packet[CSPacketField.OPTION], bytes):
            raise PacketError("Option is "
            "invalid {}.".format(self._packet[CSPacketField.OPTION]))

        if not isinstance(self._packet[CSPacketField.PAYLOAD], bytes):
            raise PacketError("Payload is "
            "invalid {}.".format(self._packet[CSPacketField.PAYLOAD]))

        packet = b""
        packet += self._packet[CSPacketField.PROTOCOL].value.to_bytes(INT_SIZE, "big")

        packet += self._packet[CSPacketField.STATE].value.to_bytes(INT_SIZE, "big")

        packet += len(self._packet[CSPacketField.OPTION]).to_bytes(INT_SIZE, "big")
        packet += self._packet[CSPacketField.OPTION]

        packet += self._packet[CSPacketField.PAYLOAD]

        return packet

    def protocol(self, protocol: Protocols = None) -> Protocols:
        from csbuilder.pool import Pool

        if protocol == None:
            return self._packet[CSPacketField.PROTOCOL]

        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols, None)

        if protocol not in Pool.get_protocols():
            raise PoolError("Protocol {} has not defined yet.".format(protocol))

        self._packet[CSPacketField.PROTOCOL] = protocol

    def state(self, state: States = None) -> States:
        from csbuilder.pool import Pool
        if state == None:
            return self._packet[CSPacketField.STATE]

        protocol = self._packet[CSPacketField.PROTOCOL]
        if protocol is None:
            raise PacketError("The packet must have protocol before.")

        if not isinstance(state, States):
            raise HTypeError("state", state, States, None)

        roles = Pool.get_roles(protocol)
        for role in roles:
            states = Pool.get_states(protocol, role)
            if state in states:
                self._role = role

        if self._role is None:
            raise PacketError("Protocol {} and state {} "
            "are mismatched.".format(protocol, state))

        self._packet[CSPacketField.STATE] = state

    def option(self, option: bytes = None) -> bytes:
        if option == None:
            return self._packet[CSPacketField.OPTION]

        if not isinstance(option, bytes):
            raise HTypeError("option", option, bytes, None)

        self._packet[CSPacketField.OPTION] = option

    def update_option(self, option: bytes) -> None:
        if not isinstance(option, bytes):
            raise HTypeError("option", option, bytes)

        self._packet[CSPacketField.OPTION] += option

    def payload(self, payload: bytes = None) -> bytes:
        if payload is None:
            return self._packet[CSPacketField.PAYLOAD]

        if not isinstance(payload, bytes):
            raise HTypeError("payload", payload, bytes, None)

        self._packet[CSPacketField.PAYLOAD] = payload

    def update_payload(self, payload: bytes):
        if not isinstance(payload, bytes):
            raise HTypeError("payload", payload, bytes)

        self._packet[CSPacketField.PAYLOAD] += payload

    def role(self) -> Roles:
        return self._role
