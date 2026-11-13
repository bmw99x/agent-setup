from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.bookings.schemas import BookingRead, BookingRequest
from app.clock import utcnow
from app.db import get_session

router = APIRouter(prefix="/bookings", tags=["bookings"])

NIGHTLY_RATE_CENTS = {"single": 8_000, "double": 12_000, "suite": 25_000}


@router.post("", status_code=201, response_model=BookingRead)
def create_booking(body: BookingRequest, session: Session = Depends(get_session)):
    starts_at = body.starts_at
    if starts_at.tzinfo is not None:
        starts_at = starts_at.astimezone(UTC).replace(tzinfo=None)
    if starts_at <= utcnow():
        raise HTTPException(status_code=422, detail="booking must start in the future")
    booking = Booking(
        guest_name=body.guest_name,
        room_type=body.room_type,
        starts_at=starts_at,
        nights=body.nights,
        price_cents=body.nights * NIGHTLY_RATE_CENTS[body.room_type],
    )
    session.add(booking)
    session.commit()
    return booking


@router.get("", response_model=list[BookingRead])
def list_bookings(session: Session = Depends(get_session)):
    return session.scalars(select(Booking).order_by(Booking.starts_at)).all()


@router.get("/{booking_id}", response_model=BookingRead)
def read_booking(booking_id: int, session: Session = Depends(get_session)):
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="booking not found")
    return booking
