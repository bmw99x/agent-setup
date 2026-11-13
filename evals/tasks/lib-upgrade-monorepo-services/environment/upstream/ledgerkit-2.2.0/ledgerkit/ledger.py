from decimal import Decimal
from dataclasses import dataclass, field

from ledgerkit.money import Money


@dataclass
class Ledger:
    currency: str
    _balances: dict[str, Money] = field(default_factory=dict)

    def post(self, debit: str, credit: str, money: Money, memo: str = "") -> None:
        zero = Money(money.amount * 0, money.currency)
        self._balances[debit] = self._balances.get(debit, zero) + money
        self._balances[credit] = self._balances.get(credit, zero) + Money(-money.amount, money.currency)

    def balance(self, account: str) -> Money:
        return self._balances.get(account, Money(Decimal(0), self.currency))
