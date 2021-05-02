from typing import Tuple

from hks_pylib.logger.standard import StdLevels, StdUsers
from csbuilder.cspacket.cspacket import CSPacket
from csbuilder.session.session import Session

from csbuilder.errors import CSError
from csbuilder.errors.session import InProcessError


class ActiveSession(Session):
    def begin(self, *args, **kwargs) -> Tuple[str, CSPacket]:
        if self._is_running:
            raise InProcessError("The session is running, cannot call again.")

        des, packet = self._activation(*args, **kwargs)
        if packet is not None:
            self._print(StdUsers.DEV, StdLevels.DEBUG, "Calling activate() session")
            super().begin()
        else:
            raise CSError("The packet is None, it can not begin the session.")

        return des, packet
