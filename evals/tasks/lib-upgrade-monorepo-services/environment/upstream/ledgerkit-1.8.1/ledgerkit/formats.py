from ledgerkit.money import Money

_SYMBOLS = {"GBP": "£", "EUR": "€", "USD": "$"}


def format_money(money: Money, locale: str = "en_GB") -> str:
    amount = f"{money.amount:,.2f}"
    if locale.startswith("de"):
        amount = amount.replace(",", "_").replace(".", ",").replace("_", ".")
        return f"{amount} {_SYMBOLS.get(money.currency, money.currency)}"
    return f"{_SYMBOLS.get(money.currency, money.currency)}{amount}"
