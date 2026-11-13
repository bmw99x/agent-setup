from payouts.http import Request, Response, route
from payouts.ledger import InsufficientBalance
from payouts.service import PayoutRejected
from payouts.wiring import payout_service


@route("POST", "/payouts")
def create_payout(request: Request) -> Response:
    try:
        payout = payout_service().request(request.json["account_id"], int(request.json["amount_pence"]))
    except PayoutRejected as error:
        return Response(422, {"error": str(error)})
    except InsufficientBalance:
        return Response(409, {"error": "insufficient balance"})
    return Response(201, {"id": payout.id, "status": payout.status})
