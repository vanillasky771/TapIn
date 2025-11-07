
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import List
from sqlmodel import Session, select
from app.database import init_db, settings
from app.models import Event, Member, EventMemberLink
from app.schemas import (
    EventCreate, EventRead, EventUpdate,
    MemberCreate, MemberRead, MemberUpdate, MemberInEventRead,
    TapInInput, MemberReadWithEvents, GradeInput, EventWithGrade, PointsAdjustInput, RecardInput,
    GradeAspectsInput, EventWithScore, MemberDetailWithEvents
)
from app.deps import get_db, must_get_event, must_get_member

app = FastAPI(title="Events & Members API (SQLite)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/healthz")
def health():
    return {"status": "ok"}

# ===================== EVENTS =====================
@app.get("/events", response_model=List[EventRead])
def list_events(db: Session = Depends(get_db)):
    return db.exec(select(Event).order_by(Event.starts_at.desc())).all()

@app.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    event = Event(**data.model_dump(by_alias=False))
    db.add(event); db.commit(); db.refresh(event)
    return event

@app.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    return must_get_event(event_id, db)

@app.post("/events/{event_id}", response_model=EventRead)
def update_event_post(event_id: int, data: EventUpdate, db: Session = Depends(get_db)):
    event = must_get_event(event_id, db)
    updates = data.model_dump(exclude_unset=True, by_alias=False)
    updates.pop("id", None)
    for k, v in updates.items():
        setattr(event, k, v)
    db.add(event); db.commit(); db.refresh(event)
    return event

@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = must_get_event(event_id, db)
    db.delete(event); db.commit()
    return None

# ===================== MEMBERS =====================
@app.get("/members", response_model=List[MemberRead])
def list_members(db: Session = Depends(get_db)):
    return db.exec(select(Member).order_by(Member.name.asc())).all()

@app.get("/members/{card_id}", response_model=MemberDetailWithEvents)
def get_member_by_card(card_id: str, db: Session = Depends(get_db)):
    # 1) find member by cardId
    member = db.exec(select(Member).where(Member.card_id == card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this cardId not found")

    # 2) get all events this member joined, including grading fields
    rows = db.exec(
        select(
            Event,
            EventMemberLink.score,
            EventMemberLink.notes,
            EventMemberLink.disiplin,
            EventMemberLink.tanggung_jawab,
            EventMemberLink.percaya_diri,
            EventMemberLink.keaktifan,
            EventMemberLink.tapped_at
        )
        .join(EventMemberLink, EventMemberLink.event_id == Event.id)
        .where(EventMemberLink.member_id == member.id)
        .order_by(Event.starts_at.desc())
    ).all()

    events: list[EventWithScore] = []
    for e, score, notes, d, tj, pd, k, tapped_at in rows:
        # base event fields (id, title, datetime, status, basicPoint)
        base = EventRead.model_validate(e).model_dump(by_alias=True)
        # build EventWithScore using field names (aliases handled by Pydantic)
        events.append(
            EventWithScore(
                **base,
                score=score,
                notes=notes,
                disiplin=d,
                tanggung_jawab=tj,
                percaya_diri=pd,
                keaktifan=k,
                tapped_at=tapped_at.replace(microsecond=0) if tapped_at else None
            )
        )

    # 3) base member fields (id, cardId, points, totalScore, etc.)
    member_base = MemberRead.model_validate(member).model_dump(by_alias=True)

    # 4) return member + events
    result = MemberDetailWithEvents(**member_base, events=events)
    # optional debug
    # print("DEBUG member detail:", result)
    return result

def list_members(db: Session = Depends(get_db)):
    return db.exec(select(Member).order_by(Member.name.asc())).all()

@app.post("/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_member(data: MemberCreate, db: Session = Depends(get_db)):
    member = Member(**data.model_dump(by_alias=False))
    db.add(member); db.commit(); db.refresh(member)
    return member


@app.post("/members/{card_id}", response_model=MemberRead)
def update_member_post_by_card(card_id: str, data: MemberUpdate, db: Session = Depends(get_db)):
    member = db.exec(select(Member).where(Member.card_id == card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this cardId not found")
    updates = data.model_dump(exclude_unset=True, by_alias=False)
    # don't allow changing identity fields
    updates.pop("id", None)
    updates.pop("card_id", None)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    for k, v in updates.items():
        setattr(member, k, v)
    db.add(member); db.commit(); db.refresh(member)
    return member


@app.delete("/members/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member_by_card(card_id: str, db: Session = Depends(get_db)):
    member = db.exec(select(Member).where(Member.card_id == card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this cardId not found")
    db.delete(member); db.commit()
    return None

# ================ TAP-IN & LIST MEMBERS OF EVENT ================
@app.post("/events/{event_id}/tapin", status_code=status.HTTP_201_CREATED)
def tap_in(event_id: int, payload: TapInInput, db: Session = Depends(get_db)):
    event = must_get_event(event_id, db)
    member = db.exec(select(Member).where(Member.card_id == payload.card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this cardId not found")

    existing = db.exec(
        select(EventMemberLink).where(
            EventMemberLink.event_id == event.id,
            EventMemberLink.member_id == member.id
        )
    ).first()

    if existing:
        # already joined -> don't add points again
        return {"message": "Already joined", "event_id": event.id, "cardId": member.card_id, "tapped_at": existing.tapped_at}

    # new join: award basicPoint
    link = EventMemberLink(event_id=event.id, member_id=member.id)
    db.add(link)

    # award points
    member.points = (member.points or 0) + (event.basic_point or 0)

    db.add(member)
    db.commit()
    return {"message": "Tap-in recorded", "event_id": event.id, "cardId": member.card_id, "tapped_at": link.tapped_at}

@app.get("/events/{event_id}/members", response_model=List[MemberInEventRead])
def list_members_of_event(event_id: int, db: Session = Depends(get_db)):
    _ = must_get_event(event_id, db)
    rows = db.exec(
        select(
            Member,
            EventMemberLink.score,
            EventMemberLink.notes,
            EventMemberLink.disiplin,
            EventMemberLink.tanggung_jawab,
            EventMemberLink.percaya_diri,
            EventMemberLink.keaktifan,
            EventMemberLink.tapped_at
        )
        .join(EventMemberLink, EventMemberLink.member_id == Member.id)
        .where(EventMemberLink.event_id == event_id)
        .order_by(Member.name.asc())
    ).all()
    
    result: list[MemberInEventRead] = []
    for m, score, notes, d, tj, pd, k, tapped_at in rows:
        # turn Member model into dict using aliases (cardId, noHandphone, totalScore, etc.)
        base = MemberRead.model_validate(m).model_dump(by_alias=True)

        # now inject the per-event fields using FIELD NAMES, not aliases
        result.append(
            MemberInEventRead(
                **base,
                score=score,
                notes=notes,
                disiplin=d,
                tanggung_jawab=tj,   # <-- use "tanggung_jawab" (field name)
                percaya_diri=pd,     # <-- use "percaya_diri" (field name)
                keaktifan=k,
                tapped_at=tapped_at.replace(microsecond=0) if tapped_at else None
            )
        )
    print("DEBUG result:", result)
    return result

@app.post("/events/{event_id}/grade", status_code=status.HTTP_200_OK)
def grade_member_in_event(event_id: int, payload: GradeInput, db: Session = Depends(get_db)):
    # ensure event exists
    event = must_get_event(event_id, db)

    # find member by cardId
    member = db.exec(select(Member).where(Member.card_id == payload.card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this cardId not found")

    # find or create link (tap-in) first
    link = db.exec(
        select(EventMemberLink).where(
            EventMemberLink.event_id == event.id,
            EventMemberLink.member_id == member.id
        )
    ).first()
    if not link:
        link = EventMemberLink(event_id=event.id, member_id=member.id)

    # set grade
    link.score = payload.score
    link.notes = payload.notes

    db.add(link)
    db.commit()

    return {
        "message": "Grade saved",
        "event_id": event.id,
        "cardId": member.card_id,
        "score": link.score,
        "notes": link.notes,
    }

@app.post("/members/{card_id}/points/add")
def add_points(card_id: str, payload: PointsAdjustInput, db: Session = Depends(get_db)):
    member = db.exec(select(Member).where(Member.card_id == card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this cardId not found")
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be > 0")
    member.points = (member.points or 0) + payload.amount
    db.add(member); db.commit(); db.refresh(member)
    return {"message": "Points added", "cardId": member.card_id, "balance": member.points}

@app.post("/members/{card_id}/points/redeem")
def redeem_points(card_id: str, payload: PointsAdjustInput, db: Session = Depends(get_db)):
    member = db.exec(select(Member).where(Member.card_id == card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this cardId not found")
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be > 0")
    if (member.points or 0) < payload.amount:
        raise HTTPException(status_code=400, detail="insufficient points")
    member.points -= payload.amount
    db.add(member); db.commit(); db.refresh(member)
    return {"message": "Points redeemed", "cardId": member.card_id, "balance": member.points}

@app.post("/events/{event_id}/grade/aspects", status_code=200)
def grade_aspects(event_id: int, payload: GradeAspectsInput, db: Session = Depends(get_db)):
    event = must_get_event(event_id, db)
    member = db.exec(select(Member).where(Member.card_id == payload.card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this cardId not found")

    link = db.exec(
        select(EventMemberLink).where(
            EventMemberLink.event_id == event.id,
            EventMemberLink.member_id == member.id
        )
    ).first()
    if not link:
        # Auto-create the link but DO NOT add basic points here (grading is separate)
        link = EventMemberLink(event_id=event.id, member_id=member.id)
        db.add(link)
        db.flush()

    # previous total to adjust member.total_score correctly
    prev_total = link.score or 0
    new_total = int(payload.disiplin) + int(payload.tanggung_jawab) + int(payload.percaya_diri) + int(payload.keaktifan)

    # update link fields
    link.disiplin = payload.disiplin
    link.tanggung_jawab = payload.tanggung_jawab
    link.percaya_diri = payload.percaya_diri
    link.keaktifan = payload.keaktifan
    link.score = new_total
    link.notes = payload.notes

    # adjust member aggregate total_score by the delta
    member.total_score = (member.total_score or 0) + (new_total - prev_total)

    db.add_all([link, member]); db.commit()
    return {"message": "Grade saved", "event_id": event.id, "cardId": member.card_id, "score": new_total}

@app.post("/members/{old_card_id}/recard")
def recard_member(old_card_id: str, payload: RecardInput, db: Session = Depends(get_db)):
    member = db.exec(select(Member).where(Member.card_id == old_card_id)).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member with this old cardId not found")

    exists = db.exec(select(Member).where(Member.card_id == payload.new_card_id)).first()
    if exists:
        raise HTTPException(status_code=400, detail="newCardId already in use")

    member.card_id = payload.new_card_id
    db.add(member); db.commit(); db.refresh(member)
    return {"message": "cardId updated", "oldCardId": old_card_id, "newCardId": member.card_id}