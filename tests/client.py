import time
import threading

from csbuilder.session import SessionManager
from csbuilder.client import ClientResponser
from hks_pylib.cipher import NoCipher, XorCipher
from hks_pylib.logger import StandardLoggerGenerator

from scheme_definition import SchemeAuthenticateClient
from scheme_type_definition import ExtendedExternalSchemeType, ExtendedInternalSchemeType

if __name__ == "__main__":
    logger_generator = StandardLoggerGenerator("client.csbuilder.log")
    session_manager = SessionManager(
            ExtendedExternalSchemeType(),
            ExtendedInternalSchemeType(),
            name="Client",
            logger_generator=logger_generator,
            display={"dev": ["warning", "debug", "error", "info"]}
        )

    responser = ClientResponser(
        cipher= XorCipher(b"1"),
        server_address=("127.0.0.1", 1999),
        session_manager=session_manager,
        name="Client",
        logger_generator=logger_generator,
        display={
            "user": ["info", "warning"],
            "dev": ["info", "error", "warning", "debug"]
        }
    )
    session = session_manager.create_session(
        ExtendedExternalSchemeType().AUTHENTICATE, 
        timeout=3, 
        active=True)
    session.set_scheme(SchemeAuthenticateClient(responser._forwarder.name))
    threading.Thread(target=responser.start).start()
    responser.activate(ExtendedExternalSchemeType().AUTHENTICATE, "huykingsofm", "12356")
    time.sleep(3)
    responser.close()