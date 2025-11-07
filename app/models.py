
from __future__ import annotations
from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field

class EventMemberLink(SQLModel, table=True):
    event_id: int | None = Field(default=None, foreign_key="event.id", primary_key=True)
    member_id: int | None = Field(default=None, foreign_key="member.id", primary_key=True)
    tapped_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    disiplin: int | None = None
    tanggung_jawab: int | None = None
    percaya_diri: int | None = None
    keaktifan: int | None = None
    score: int | None = None            # total of 4 aspects
    notes: str | None = None

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    subtitle: str | None = None
    starts_at: datetime = Field(index=True)
    status: str = Field(default="planned", index=True)
    basic_point: int = Field(default=0, index=True)

class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    card_id: str = Field(index=True)
    name: str = Field(index=True)
    wilayah: str | None = Field(default=None, index=True)
    lingkungan: str | None = Field(default=None, index=True)
    no_handphone: str | None = Field(default=None, index=True)
    instagram: str | None = Field(default=None)
    birthday: date | None = Field(default=None, index=True)
    age: str | None = Field(default=None, index=True)
    status: str | None = Field(default=None)

    points: int = Field(default=0, index=True)        # accumulated points
    total_score: int = Field(default=0, index=True)   # sum of all event scores for this member