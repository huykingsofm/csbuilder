from csbuilder.session import SessionManager
from csbuilder.packet import CannotExtractPacket, PacketUtil

from hks_pylib.logger import LoggerGenerator
from hks_pynetwork.internal import ChannelClosed, LocalNode


class Responser(object):
    def __init__(
                    self,
                    name:str,
                    session_manager: SessionManager,
                    logger_generator: LoggerGenerator = ...,
                    display: dict = ...
                ) -> None:
        assert isinstance(name, str)
        assert isinstance(session_manager, SessionManager)
        assert isinstance(display, dict)
        super().__init__()
        
        self._name = name

        self._session_manager = session_manager

        self._print = logger_generator.generate(
            name=name, 
            display=display
        )

        self._external_scheme_type_group = self._session_manager._external_scheme_type_group
        self._internal_scheme_type_group = self._session_manager._internal_scheme_type_group

        # Create nodes for communicating between objects in this program
        self._node = LocalNode(
            name="Node of " + name,
            logger_generator=logger_generator,
            display=display
        )

    def solve(self, source: str, packet_dict: dict):
        response, destination = self._session_manager.response(source, packet_dict)
        if response is not None:
            self._node.send(destination, response)

    def is_valid_source(self, source: str, packet_dict: dict):
        if packet_dict["scheme"] not in self._external_scheme_type_group and\
            packet_dict["scheme"] not in self._internal_scheme_type_group:
            self._print("dev", "warning", "Packet scheme is unknown ({})".format(packet_dict["scheme"]))
            return False

        return True

    def activate(self, activated_scheme_type: int, *args):
        response_packet, des = self._session_manager.activate(activated_scheme_type, *args)
        if response_packet is None or des is None:
            return False
        self._node.send(des, response_packet)
        return True


    def start(self):
        self._print("user", "info", "Responser starts...")
        self._print("dev", "info", "Responser started")
        while True:
            try:
                source, data, _ = self._node.recv()
                if source == None:
                    # if connection is alive, ignore error, print a warning and continue
                    self._print("dev", "warning", "Something error when source is None")
                    try:
                        self._print("dev", "debug", PacketUtil.extract(data))
                    except:
                        self._print("dev", "debug", "Cannot print received data")
                    continue
            except ChannelClosed:
                self._print("dev", "info", "Stop because Channel closed")
                break
            except Exception as e:
                self._print("user", "info", "Something errors when receving connection")
                self._print("dev", "error", "Something errors when receving connection ({})".format(repr(e)))
                break

            try:
                packet_dict = PacketUtil.extract(data)
            except CannotExtractPacket as e:
                self._print("dev", "warning", "Error when extract data ({})".format(repr(e)))
                continue
            except Exception as e:
                self._print("dev", "error", "Unknown error occurs when extract data ({})".format(repr(e)))
                break

            if not self.is_valid_source(source, packet_dict):
                continue
            
            self.solve(source, packet_dict)

        self._node.close()
        self._print("user", "info", "Responser stops")
        self._print("dev", "info", "Responser stops")

    def close(self):
        self._node.close()