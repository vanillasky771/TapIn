
from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app.models import Event, Member

def get_db(session: Session = Depends(get_session)) -> Session:
    return session

def must_get_event(event_id: int, db: Session) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event

def must_get_member(member_id: int, db: Session) -> Member:
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member
