import time

from hks_pylib.logger.logger import Display
from hks_pylib.logger.standard import StdUsers
from hks_pylib.logger import StandardLoggerGenerator

from csbuilder.cspacket import CSPacketField
from csbuilder.cspacket import CSPacket
from csbuilder.session import SessionManager
from csbuilder.session.session import Session

from tests.schemes import MyProtocols, SubmitRoles
from tests.submit_scheme import SubmitClientStates, SubmitServerStates
from tests.submit_scheme import SubmitServerScheme, SubmitClientScheme


logger_generator = StandardLoggerGenerator("tests/test_session.log")


def test_session():
    scheme = SubmitServerScheme()
    session = Session(
            scheme=scheme,
            timeout=3,
            name="Test Session",
            logger_generator=logger_generator,
            display={StdUsers.USER: Display.ALL, StdUsers.DEV: Display.ALL}
        )

    ############################################################
    print("Send send packet --> reset packet")
    send_packet = CSPacket(
            MyProtocols.SUBMIT,
            SubmitRoles.CLIENT,
            SubmitClientStates.SEND
        )
    result = session.respond("Somewhere", send_packet)
    assert result.packet == session._ignore_packet and result.destination == "Somewhere"

    ############################################################
    print("Send request packet --> return accept packet, timeout")
    request_packet = CSPacket(
            MyProtocols.SUBMIT,
            SubmitRoles.CLIENT,
            SubmitClientStates.REQUEST
        )

    result = session.respond("Somewhere", request_packet)
    assert result.packet[CSPacketField.STATE] == SubmitServerStates.ACCEPT
    assert scheme._step == "REQUESTED"
    print("Sleep 1s...")
    time.sleep(1)
    assert scheme._step == "REQUESTED"
    print("Sleep 3s...")
    time.sleep(3)
    assert scheme._step == None

    ############################################################
    print("Send request --> accept; Send send --> accept;")
    request_packet = CSPacket(
            MyProtocols.SUBMIT,
            SubmitRoles.CLIENT,
            SubmitClientStates.REQUEST
        )
    result = session.respond("Somewhere", request_packet)
    assert result.packet[CSPacketField.STATE] == SubmitServerStates.ACCEPT
    assert scheme._step == "REQUESTED"

    send_packet = CSPacket(
            MyProtocols.SUBMIT,
            SubmitRoles.CLIENT,
            SubmitClientStates.SEND
        )
    result = session.respond("Somewhere", send_packet)
    assert result.packet[CSPacketField.STATE] == SubmitServerStates.SUCCESS
    assert scheme._step == None


def set_server_session_manager():
    session_manager_server = SessionManager(
        name="Test Server Session Manager",
        logger_generator=logger_generator,
        display={StdUsers.USER: Display.ALL, StdUsers.DEV: Display.ALL}
    )

    submit_server_scheme = SubmitServerScheme()
    session_manager_server.create_session(
        scheme=submit_server_scheme,
        timeout=3
    )

    return session_manager_server, submit_server_scheme


def set_client_session_manager():
    session_manager_client = SessionManager(
            name="Test Client Session Manager",
            logger_generator=logger_generator,
            display={StdUsers.USER: Display.ALL, StdUsers.DEV: Display.ALL}
        )

    submit_client_scheme = SubmitClientScheme("Somewhere")
    session_manager_client.create_session(
            scheme=submit_client_scheme,
            timeout=3
        )

    return session_manager_client, submit_client_scheme


def test_session_manager():
    session_manager_client, client_scheme = set_client_session_manager()
    session_manager_server, server_scheme = set_server_session_manager()
    
    # Activate --> request packet
    expected_request_packet = CSPacket(
            MyProtocols.SUBMIT,
            SubmitRoles.CLIENT,
            SubmitClientStates.REQUEST
        )
    source, request_packet = session_manager_client.activate(MyProtocols.SUBMIT, SubmitRoles.CLIENT)

    assert request_packet.state() == expected_request_packet.state()
    
    # Send request packet to responser --> accept packet
    expected_accept_packet = CSPacket(
            MyProtocols.SUBMIT,
            SubmitRoles.SERVER,
            SubmitServerStates.ACCEPT
        )
    accept_result = session_manager_server.respond("Somewhere", request_packet)
    assert accept_result.packet.state() == expected_accept_packet.state()

    # Send accept packet to requester --> send packet
    expected_send_packet = CSPacket(
            MyProtocols.SUBMIT,
            SubmitRoles.CLIENT,
            SubmitClientStates.SEND
        )
    send_result = session_manager_client.respond("Somewhere", accept_result.packet)
    assert send_result.packet.state() == expected_send_packet.state()

    # Send "send" packet to responser --> success packet, responser end session
    expected_success_packet = CSPacket(
            MyProtocols.SUBMIT,
            SubmitRoles.SERVER,
            SubmitServerStates.SUCCESS
        )
    success_result = session_manager_server.respond("Somewhere", send_result.packet)
    assert success_result.packet.state() == expected_success_packet.state()

    # Send success packet to requester --> requester end session
    end_result = session_manager_client.respond("Somewhere", success_result.packet)
    assert end_result.packet is None
    assert client_scheme._step is None
    assert server_scheme._step is None


if __name__ == "__main__":
    test_session()
