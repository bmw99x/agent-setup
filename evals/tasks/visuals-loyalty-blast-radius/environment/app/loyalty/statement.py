from loyalty.ledger import PointsLedger


def statement_lines(ledger: PointsLedger, member_id: str) -> list[str]:
    """Monthly statement. Amounts were fixed by points_for at accrual time; nothing is recomputed here."""
    lines = [f"{day:%d %b}  +{points}" for day, points in ledger.entries(member_id)]
    lines.append(f"Balance: {ledger.balance(member_id)}")
    return lines
