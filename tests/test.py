import time

from csbuilder.packet import PacketGenerator
from csbuilder.const_group import ConstGroup
from csbuilder.session import SessionManager

class ConstType(ConstGroup):
    def __init__(self) -> None:
        super().__init__()
        self.NONE = 0
        self.REQUIRE = 1
        self.SUBMIT = 2

class ConstStatusClientREQUIRE(ConstGroup):
    def __init__(self) -> None:
        self.NONE = 0
        self.REQUEST = 1
        self.SUCCESS = 2
        self.FAILURE = 3
        self.RESET = 99
        super().__init__()


class ConstStatusServerREQUIRE(ConstGroup):
    def __init__(self) -> None:
        self.NONE = 0
        self.ACCEPT = 1
        self.DENY = 2
        self.RESET = 99
        super().__init__()


class RequireServerManager(object):
    def __init__(self) -> None:
        self._const_type = ConstType()
        self._const_status_require = ConstStatusServerREQUIRE()
        self._server_packet_manager = PacketGenerator(self._const_type, self._const_status_require)
        self.__in_process = False

    def none(self, packet_dict: dict, *args):
        packet = self._server_packet_manager.generate(
            self._const_type.REQUIRE, 
            self._const_status_require.RESET
        )
        self.__in_process = False
        return packet.create(), False

    def request(self, packet_dict: dict, *args):
        if not self.__in_process:
            packet = self._server_packet_manager.generate(
                self._const_type.REQUIRE, 
                self._const_status_require.ACCEPT
                )
            packet.set_data(b"huy thong minh")
            cont = True
        else:
            packet = self._server_packet_manager.generate(
                self._const_type.REQUIRE, 
                self._const_status_require.DENY
                )
            cont = False
        self.__in_process = True
        return packet.create(), cont

    def success(self, packet_dict: dict, *args):
        if not self.__in_process:
            packet = self._server_packet_manager.generate(
            self._const_type.REQUIRE, 
            self._const_status_require.RESET
            ).create()
        else:
            packet = None
        self.__in_process = False
        return packet, False

    def failure(self, packet_dict: dict, *args):
        if not self.__in_process:
            packet = self._server_packet_manager.generate(
            self._const_type.REQUIRE, 
            self._const_status_require.RESET
            ).create()
        else:
            packet = None
        self.__in_process = False
        return packet, False

    def reset(self, packet_dict: dict, *args):
        self.__in_process = False
        return None, False

class RequireClientManager(object):
    def __init__(self) -> None:
        self._const_type = ConstType()
        self._const_status_require = ConstStatusClientREQUIRE()
        self._const_status_server_require = ConstStatusServerREQUIRE()
        self._client_packet_manager = PacketGenerator(self._const_type, self._const_status_require)
        self.__in_process = False

    def initial(self, *args):
        packet = self._client_packet_manager.generate(
            self._const_type.REQUIRE,
            self._const_status_require.REQUEST
        )
        self.__in_process = True
        return packet.create(), None

    def none(self, packet_dict: dict, *args):
        packet = self._client_packet_manager.generate(
            self._const_type.REQUIRE, 
            self._const_status_require.RESET
        )
        self.__in_process = False
        return packet.create(), False

    def accept(self, packet_dict: dict, *args):
        if not self.__in_process:
            packet = self._client_packet_manager.generate(
                self._const_type.REQUIRE,
                self._const_status_require.RESET
            )
        else:
            if packet_dict["DATA"]:
                packet = self._client_packet_manager.generate(
                    self._const_type.REQUIRE,
                    self._const_status_require.SUCCESS
                )
            else:
                packet = self._client_packet_manager.generate(
                    self._const_type.REQUIRE,
                    self._const_status_require.FAILURE
                )
        self.__in_process = False
        return packet.create(), False
    
    def deny(self, packet_dict: dict, *args):
        self.__in_process = False
        return None, False
    
    def reset(self, packet_dict: dict, *args):
        self.__in_process = False
        return None, False

    def assign_to_session(self, session):
        session.assign(self._const_status_require.NONE, self.none)
        session.assign(self._const_status_server_require.ACCEPT, self.accept)
        session.assign(self._const_status_server_require.DENY, self.deny)
        session.assign(self._const_status_server_require.RESET, self.reset)
        session.assign_initial(self.initial)

def f(*args):
    if args == ():
        print("True")


class A():
    def __init__(self) -> None:
        self._x = 10

    def print(self):
        print(self._x)

class B(A):
    def __init__(self) -> None:
        super().__init__()
        self._x = 12

    @property
    def x(self):
        return self._x

if __name__ == "__main__":
    b = B()
    print(b.x)
    c = type(b)()
    print(c.x)
    """ const_type = ConstType()
    const_status_server_require = ConstStatusServerREQUIRE()
    const_status_client_require = ConstStatusClientREQUIRE()
    server_require_packet_manager = PacketManager(const_type, const_status_server_require)
    client_require_packet_manager = PacketManager(const_type, const_status_client_require)

    server_reset_packet = server_require_packet_manager.generate_packet(
        const_type.REQUIRE, 
        const_status_server_require.RESET
    )
    client_reset_packet = client_require_packet_manager.generate_packet(
        const_type.REQUIRE, 
        const_status_client_require.RESET
    )

    server_session_manager = SessionManager()
    client_session_manager = SessionManager()

    require_server_manager = RequireServerManager()
    session = server_session_manager.create_session(packet_type=const_type.REQUIRE, timeout=10, active=False)
    session.assign_reset_packet(server_reset_packet.create())
    session.assign(const_status_client_require.NONE, require_server_manager.none)
    session.assign(const_status_client_require.REQUEST, require_server_manager.request)
    session.assign(const_status_client_require.FAILURE, require_server_manager.failure)
    session.assign(const_status_client_require.SUCCESS, require_server_manager.success)
    session.assign(const_status_client_require.RESET, require_server_manager.reset)
    session.assign_initial(const_status_client_require.REQUEST)

    require_client_manager = RequireClientManager()
    session = client_session_manager.create_session(const_type.REQUIRE, timeout= 1, active= True)
    session.assign_reset_packet(client_reset_packet.create())
    session.assign(const_status_server_require.NONE, require_client_manager.none)
    session.assign(const_status_server_require.ACCEPT, require_client_manager.accept)
    session.assign(const_status_server_require.DENY, require_client_manager.deny)
    session.assign(const_status_server_require.RESET, require_client_manager.reset)
    session.assign_initial(require_client_manager.initial)

    packet = client_session_manager.activate(const_type.REQUIRE)
    if packet is None:
        exit(0)
    
    packet_dict = server_require_packet_manager.extract(packet)
    print("From Client: ", packet_dict)
    time.sleep(3)
    packet = server_session_manager.response(packet_dict)
    if packet is None:
        exit(0)
    
    packet_dict = client_require_packet_manager.extract(packet)
    print("From Server: ", packet_dict)
    packet = client_session_manager.response(packet_dict)
    if packet is None:
        exit(0)
    
    packet_dict = server_require_packet_manager.extract(packet)
    print("From Client: ", packet_dict)
    packet = server_session_manager.response(packet_dict)
    if packet is None:
        exit(0)

    packet_dict = client_require_packet_manager.extract(packet)
    print("From Server: ", packet_dict)
    packet = client_session_manager.response(packet_dict)
    if packet is None:
        exit(0) """