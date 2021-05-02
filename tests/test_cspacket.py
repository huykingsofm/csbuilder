from tests.schemes import ControlRoles, MyProtocols, SubmitRoles
from tests.control_scheme import ControlDriverStatusGroup
from tests.submit_scheme import SubmitServerStates, SubmitClientStates

from csbuilder.cspacket.util import CSPacketUtil
from csbuilder.cspacket import CSPacketUtil, CSPacket
from csbuilder.cspacket.cspacket import CSPacketField



def test_cspacket():
    packet = CSPacket(MyProtocols.SUBMIT, SubmitServerStates.IGNORE)
    print(MyProtocols.SUBMIT)
    print(packet)
    assert packet.to_bytes() == b"\x00\x01\x00\x00\x00\x00"
    assert packet.to_bytes() and packet.role() == SubmitRoles.SERVER


def test_cspacketextractor_extract():
    packet = CSPacket(MyProtocols.CONTROL, ControlDriverStatusGroup.REQUEST)
    data = packet.to_bytes()
    packet_dict = CSPacketUtil.extract(data, role=ControlRoles.DRIVER)
    assert packet_dict[CSPacketField.PROTOCOL] in MyProtocols
    assert packet_dict[CSPacketField.PROTOCOL] == MyProtocols.CONTROL
    assert packet_dict[CSPacketField.STATE] in ControlDriverStatusGroup
    assert packet_dict[CSPacketField.STATE] == ControlDriverStatusGroup.REQUEST


def test_cspacketextractor_check():
    packet = CSPacket(MyProtocols.SUBMIT, SubmitServerStates.DENY)
    data = packet.to_bytes()
    result = CSPacketUtil.check(
            data,
            MyProtocols.SUBMIT,
            SubmitServerStates.DENY,
            role=SubmitRoles.SERVER
        )
    assert result == True

    result = CSPacketUtil.check(
            data,
            MyProtocols.SUBMIT,
            SubmitServerStates.ACCEPT,
            SubmitRoles.SERVER
        )
    assert result == False and result.field == CSPacketField.STATE

    try:
        result = CSPacketUtil.check(
                data,
                MyProtocols.CONTROL,
                SubmitServerStates.DENY,
                SubmitRoles.SERVER
            )
        assert True
    except:
        pass

def test_csenum():
    print(MyProtocols.values())
    print(SubmitClientStates.values())
    print(SubmitServerStates.names())


if __name__ == "__main__":
    test_cspacketextractor_extract()