import os
from dataclasses import dataclass

TEST_KEY_PREFIX = "sk_test_"


class GatewayConfigError(ValueError):
    pass


@dataclass(frozen=True)
class GatewayConfig:
    api_key: str
    test_mode: bool = False

    def __post_init__(self) -> None:
        if self.test_mode and not self.api_key.startswith(TEST_KEY_PREFIX):
            raise GatewayConfigError("test_mode requires an sk_test_ key")

    @classmethod
    def from_env(cls, *, test_mode: bool = False) -> "GatewayConfig":
        return cls(api_key=os.environ["PAYMENTS_API_KEY"], test_mode=test_mode)
