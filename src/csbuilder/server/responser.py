import threading
from typing import Iterable

from hks_pylib.logger import LoggerGenerator, InvisibleLoggerGenerator

from hks_pynetwork.external import STCPSocket
from hks_pynetwork.internal import ForwardNode

from csbuilder.responser import Responser

from hkserror.hkserror import HTypeError, HFormatError


class ServerResponser(Responser):
    def __init__(
                    self,
                    socket: STCPSocket,
                    address: tuple,
                    logger_generator: LoggerGenerator = InvisibleLoggerGenerator(),
                    display: dict = {}
                ) -> None:
        if not isinstance(socket, STCPSocket):
            raise HTypeError("socket", socket, STCPSocket)

        if not isinstance(address, (Iterable)):
            raise HTypeError("address", address, Iterable)

        if len(address) != 2:
            raise HFormatError("Parameter address expected an "
            "pair of two elements - (ip/hostname/domain, port).")

        if not isinstance(logger_generator, LoggerGenerator):
            raise HTypeError("logger_generator", logger_generator, LoggerGenerator)

        if not isinstance(display, dict):
            raise HTypeError("display", display, dict)

        super().__init__(
                logger_generator=logger_generator,
                display=display,
                name="Server Reponser [{}]".format(address)
           )

        self._socket = socket
        self._address = address
        self._forwarder = ForwardNode(
                self._node,
                self._socket,
                name= "Forwarder of {}".format(self._name),
                implicated_die=True,
                logger_generator=logger_generator,
                display=display
            )
        threading.Thread(
                target=self._forwarder.start,
                name="Thread forwarder of {}".format(self._name)
            ).start()

    def close(self) -> None:
        self._socket.close()
        self._forwarder.close()
        return super().close()
