from csbuilder.server import Listener, ServerResponser
from hks_pylib.logger import StandardLoggerGenerator
from hks_pylib.cipher import XorCipher

from scheme_definition import SchemeAuthenticateServer
from scheme_type_definition import ExtendedInternalSchemeType, ExtendedExternalSchemeType

if __name__ == "__main__":
    logger_generator = StandardLoggerGenerator("server.csbuilder.log")

    listener = Listener(
        cipher=XorCipher(b"1"),
        server_address=("127.0.0.1", 1999),
        external_scheme_type_group=ExtendedExternalSchemeType(),
        internal_scheme_type_group=ExtendedInternalSchemeType(),
        responser_cls=ServerResponser,
        logger_generator=logger_generator,
        display={
            "user": ["info", "warning"],
            "dev": ["info", "error", "warning", "debug"]
        }
    )
    session_manager = listener.session_manager
    session = session_manager.create_session(
        ExtendedExternalSchemeType().AUTHENTICATE,
        timeout=3,
        active=False)
    session.set_scheme(SchemeAuthenticateServer())
    listener.start()
    #threading.Thread(target=listener.start).start()