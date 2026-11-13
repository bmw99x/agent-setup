from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.db import get_session
from app.members.repository import MemberRepository
from app.members.schemas import MemberRead, MemberRegistration
from app.members.service import MemberService

router = APIRouter(prefix="/members", tags=["members"])


def get_member_service(session: Session = Depends(get_session)) -> MemberService:
    return MemberService(MemberRepository(session))


@router.post("", status_code=201, response_model=MemberRead)
def register_member(body: MemberRegistration, service: MemberService = Depends(get_member_service)):
    return service.register(body.email, body.name)


@router.get("/{member_id}", response_model=MemberRead)
def read_member(member_id: int, service: MemberService = Depends(get_member_service)):
    try:
        return service.get(member_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="member not found") from None
