import threading
import time

from hks_pylib.logger.standard import StdUsers

from tests.schemes import MyProtocols
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
    listener.session_manager().create_session(
        scheme=SubmitServerScheme(),
        timeout=3,
        logger_generator=logger_generator,
        display={StdUsers.USER: Display.ALL, StdUsers.DEV: Display.ALL}
    )

    listener.listen()
    listener.accept()
    listener.close()

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
        scheme=SubmitClientScheme(client._forwarder.name),
        timeout=3,
        logger_generator=logger_generator,
        display={StdUsers.USER: Display.ALL, StdUsers.DEV: Display.ALL}
    )

    client.connect()
    client.start(True)
    print("ACTIVATE's RESULT:", client.activate(MyProtocols.SUBMIT))
    print("SCHEME's RESULT:", client.wait_result(MyProtocols.SUBMIT))
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