from hks_pylib.done import Done
from csbuilder.const_group import ConstGroup


class CannotExtractPacket(Exception):
    ...


class Packet(object):
    """
    Packet
    ============
    The class is used to create a simple network packet.

    You should use the `PacketGenerator` to generate packets rather than directly using the `Packet`.

    ----------------
    The struct of the packet in this class is:
    - scheme type (2 bytes)
    - status (2 bytes)
    - optional header lenght (2 bytes)
    - optional header (variable length)
    - data (variable length)
    ----------------
    Methods:
    - `__init__(self, scheme_type: int, status: int)`: initialize a packet with provided type and status
    - `append_optional_header(self, value: bytes)`: append a optional value to optional header.
    - `clear_optional_header(self)`: clear all values in optional header.
    - `set_data(self, data: bytes)`: set the data in packet to a provided value.
    - `append_data(self, data: bytes)`: append a value to current data.
    - `create(self)`: generate a packet in bytes responding to provided parameters.
    """
    def __init__(self, scheme_type: int, status: int):
        assert isinstance(scheme_type, int)
        assert isinstance(status, int)

        self.__scheme_type = scheme_type
        self.__status = status
        self.__optional_header = b""
        self.__data = b""

    def append_optional_header(self, value: bytes):
        assert isinstance(value, bytes)
        self.__optional_header += value

    def clear_optional_header(self):
        self.__optional_header = b""

    def set_data(self, data: bytes):
        assert isinstance(data, bytes)
        self.__data = data

    def append_data(self, data: bytes):
        assert isinstance(data, bytes)
        self.__data += data

    def create(self):
        packet = b""
        packet += self.__scheme_type.to_bytes(2, "big")
        packet += self.__status.to_bytes(2, "big")

        packet += len(self.__optional_header).to_bytes(2, "big")
        packet += self.__optional_header

        packet += self.__data

        return packet


class PacketGenerator(object):
    """
    PacketGenerator
    ==============
    A class is built for packet generating of a scheme.
    You should use `PacketGenerator` to generate packets rather than directly using `_Packet`.

    -----------------------
    Methods:
    - `__init__(self, scheme_type: int, status_group: ConstGroup)`: 
    initialize the `PacketGenerator` object with 
    provided scheme type and status group (object of `ConstGroup` class).
    - `generate(self, status: int):` A wrapper to generate a `_Packet` object.
    -----------------------
    """
    def __init__(
            self,
            scheme_type: int,
            status_group: ConstGroup
        ):
        self.__scheme_type = scheme_type
        self.__status_group = status_group
        
    def generate(self, status: int):
        assert status in self.__status_group
        return Packet(self.__scheme_type, status)

class PacketUtil(object):
    scheme_status = {}
    scheme_name = {}

    @staticmethod
    def add_scheme(
            scheme_type: int,
            scheme_name:str,
            client_status_group: ConstGroup,
            server_status_group: ConstGroup
            ):
        assert isinstance(scheme_type, int)
        assert isinstance(scheme_name, str)
        assert isinstance(client_status_group, ConstGroup)
        assert isinstance(server_status_group, ConstGroup)
        assert scheme_type not in PacketUtil.scheme_name.keys()
        assert scheme_name not in PacketUtil.scheme_name.values()

        PacketUtil.scheme_status[scheme_type] = {
            "client": client_status_group,
            "server": server_status_group
        }
        PacketUtil.scheme_name[scheme_type] = scheme_name

    @staticmethod
    def extract(data: bytes):
        assert isinstance(data, bytes)

        packet_dict = {}
        b_scheme_type = data[0: 2]
        if not b_scheme_type:
            raise CannotExtractPacket("Scheme type is not provided")
        packet_dict["scheme"] = int.from_bytes(b_scheme_type, "big")

        b_status = data[2: 4]
        if not b_status:
            raise CannotExtractPacket("Status is not provided")
        packet_dict["status"] = int.from_bytes(b_status, "big")

        b_optional_length = data[4: 6]
        if not b_optional_length:
            raise CannotExtractPacket("Optional length is not provided")
        option_length = int.from_bytes(b_optional_length, "big")

        b_option = data[6: 6 + option_length]
        if len(b_option) < option_length:
            raise CannotExtractPacket("Optional header is not enough length")
        packet_dict["option"] = data[6: 6 + option_length]

        packet_dict["data"] = data[6 + option_length:]

        return packet_dict

    @staticmethod
    def check(data: bytes, expected_scheme: int, expected_status: int, side: str = "client", is_dict: bool = False):
        assert side in ("client", "server")
        assert expected_scheme in PacketUtil.scheme_status.keys()
        assert expected_status in PacketUtil.scheme_status[expected_scheme][side]

        if is_dict:
            packet_dict = data
        else:
            packet_dict = PacketUtil.extract(data)
        if packet_dict["scheme"] != expected_scheme:
            return Done(False,
                        wrong_field="scheme",
                        actual=PacketUtil.scheme_name.get(packet_dict["scheme"], "Unknown"),
                        expected=PacketUtil.scheme_name.get[expected_scheme]
                    )

        if packet_dict["status"] != expected_status:
            status_group = PacketUtil.scheme_status[expected_scheme][side]
            return Done(False,
                        wrong_field="status",
                        actual=status_group._dict.get(packet_dict["status"], "Unknown"),
                        expected=status_group._dict[expected_status])

        return Done(True)
