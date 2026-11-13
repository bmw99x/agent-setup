from collections.abc import Iterable, Mapping, Sequence

HEADER = ("id", "name", "email")


def format_row(values: Sequence[object]) -> str:
    return ",".join(str(value) for value in values)


def export_rows(customers: Iterable[Mapping[str, object]]) -> str:
    lines = [format_row(HEADER)]
    lines.extend(format_row([customer[column] for column in HEADER]) for customer in customers)
    return "\n".join(lines) + "\n"
