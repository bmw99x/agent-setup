import sys
from datetime import date

from app.shipping.eta import est_delivery, latest_delivery
from app.shipping.fees import delivery_fee


def main(argv: list[str]) -> None:
    dispatched_on, service, weight = date.fromisoformat(argv[0]), argv[1], float(argv[2])
    print(f"fee:    {delivery_fee(weight)}p")
    print(f"eta:    {est_delivery(dispatched_on, service):%a %d %b}")
    print(f"latest: {latest_delivery(dispatched_on, service):%a %d %b}")


if __name__ == "__main__":
    main(sys.argv[1:])
