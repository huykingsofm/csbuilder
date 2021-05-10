from tests.schemes import ControlRoles, MyProtocols, SubmitRoles
from tests.control_scheme import ControlDriverStatusGroup
from tests.submit_scheme import SubmitServerStates

from csbuilder.cspacket import CSPacket
from csbuilder.cspacket.cspacket import CSPacketField



def test_cspacket():
    packet = CSPacket(MyProtocols.SUBMIT, SubmitRoles.SERVER, SubmitServerStates.IGNORE)
    print(MyProtocols.SUBMIT)
    print(packet)
    assert packet.to_bytes() == b"\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
    assert packet.to_bytes() and packet.role() == SubmitRoles.SERVER


def test_cspacketextractor_extract():
    packet = CSPacket(MyProtocols.CONTROL, ControlRoles.DRIVER, ControlDriverStatusGroup.REQUEST)
    data = packet.to_bytes()
    packet_dict = CSPacket.from_bytes(data)
    assert packet_dict[CSPacketField.PROTOCOL] in MyProtocols
    assert packet_dict[CSPacketField.PROTOCOL] == MyProtocols.CONTROL
    assert packet_dict[CSPacketField.STATE] in ControlDriverStatusGroup
    assert packet_dict[CSPacketField.STATE] == ControlDriverStatusGroup.REQUEST

if __name__ == "__main__":
    test_cspacketextractor_extract()