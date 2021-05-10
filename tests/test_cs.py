from socket import timeout
import threading
import time

from hks_pylib.logger.standard import StdUsers
from tests import schemes

from tests.schemes import MyProtocols, SubmitRoles
from tests.submit_scheme import SubmitServerScheme, SubmitClientScheme

from csbuilder.server import Listener
from csbuilder.client import ClientResponser

from hks_pylib.logger import Display
from hks_pylib.logger import StandardLoggerGenerator
from hks_pylib.cryptography.ciphers.symmetrics import AES_CTR

KEY = b"0123456789abcdeffedcba9876543210"

def run_listener():
    logger_generator = StandardLoggerGenerator("tests/test_server.log")
    listener = Listener(
        name="Listener",
        cipher=AES_CTR(KEY),
        address=("127.0.0.1", 1999),
        logger_generator=logger_generator,
        display={StdUsers.USER: Display.ALL, StdUsers.DEV: Display.ALL}
    )
    listener.session_manager().create_session(scheme=SubmitServerScheme())
    listener.session_manager().create_session(scheme=SubmitClientScheme())
    listener.listen()

    responser = listener.accept(False)
    responser.session_manager().get_scheme(MyProtocols.SUBMIT, SubmitRoles.SERVER).config(
            forwarder_name = responser._forwarder.name
        )
    responser.session_manager().get_scheme(MyProtocols.SUBMIT, SubmitRoles.CLIENT).config(
            responser._forwarder.name
        )
    responser.start(True)
    result = responser.activate(MyProtocols.SUBMIT, SubmitRoles.CLIENT)
    print("ACTIVATE RESULT", result)
    listener.close()
    print(responser.wait_result(MyProtocols.SUBMIT, SubmitRoles.CLIENT, timeout = 5))
    responser.close()

def run_client():
    logger_generator = StandardLoggerGenerator("tests/test_client.log")

    client = ClientResponser(
        name="Client Responser",
        cipher=AES_CTR(KEY),
        address=("127.0.0.1", 1999),
        logger_generator=logger_generator,
        display={StdUsers.USER: Display.ALL, StdUsers.DEV: Display.ALL}
    )

    client.session_manager().create_session(
        scheme=SubmitClientScheme(client._forwarder.name)
    )

    client.session_manager().create_session(
        scheme=SubmitServerScheme(client._forwarder.name)
    )

    client.connect()
    client.start(True)
    print("SCHEME's RESULT:", client.wait_result(
            MyProtocols.SUBMIT,
            SubmitRoles.SERVER,
            timeout = 5
            )
        )
    client.close()

def test_client_server():
    print("Start listener")
    t1 = threading.Thread(target=run_listener, name="LISTENER")
    t1.start()
    time.sleep(1)
    print("Start client")
    t2 = threading.Thread(target=run_client, name="CLIENT")
    t2.start()
    t1.join()
    t2.join()