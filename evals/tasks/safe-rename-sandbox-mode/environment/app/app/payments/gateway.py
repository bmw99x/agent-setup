import logging
from dataclasses import dataclass
from uuid import uuid4

from app.payments.config import GatewayConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Charge:
    id: str
    amount_minor: int
    captured: bool
    simulated: bool


class Gateway:
    def __init__(self, config: GatewayConfig) -> None:
        self._config = config

    @property
    def test_mode(self) -> bool:
        return self._config.test_mode

    def charge(self, amount_minor: int) -> Charge:
        if amount_minor <= 0:
            raise ValueError("amount must be positive")
        if self.test_mode:
            logger.info("test_mode: simulating charge of %s", amount_minor)
            return Charge(id=f"sim_{uuid4().hex}", amount_minor=amount_minor, captured=False, simulated=True)
        return Charge(id=f"ch_{uuid4().hex}", amount_minor=amount_minor, captured=True, simulated=False)
