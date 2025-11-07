
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

# ===== Event =====
class EventBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    title: str
    subtitle: str | None = None
    starts_at: datetime = Field(alias="datetime")
    status: str = "planned"
    basic_point: int = Field(default=0, alias="basicPoint")  # NEW
    creator_pin: str | None = Field(default=None, alias="creatorPin")

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    title: str | None = None
    subtitle: str | None = None
    starts_at: datetime | None = Field(default=None, alias="datetime")
    status: str | None = None
    basic_point: int | None = Field(default=None, alias="basicPoint")  # NEW

class EventRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int
    title: str
    subtitle: str | None
    starts_at: datetime = Field(alias="datetime")
    status: str
    basic_point: int = Field(alias="basicPoint")  # NEW
    created_by_name: str | None = None
    created_by_pin_id: int | None = None

# ===== Member =====

class MemberBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    card_id: str = Field(alias="cardId")
    name: str
    wilayah: str | None = None
    lingkungan: str | None = None
    no_handphone: str | None = Field(default=None, alias="noHandphone")
    instagram: str | None = None
    birthday: date | None = None
    age: str | None
    status: str | None
    created_by_name: str | None = None
    created_by_pin_id: int | None = None
    creator_pin: str | None = Field(default=None, alias="creatorPin")

class MemberCreate(MemberBase):
    pass

class MemberUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    card_id: str | None = Field(default=None, alias="cardId")
    name: str | None = None
    wilayah: str | None = None
    lingkungan: str | None = None
    no_handphone: str | None = Field(default=None, alias="noHandphone")
    instagram: str | None = None
    birthday: date | None = None
    age: str | None
    status: str | None

class MemberRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int
    card_id: str = Field(alias="cardId")
    name: str
    wilayah: str | None
    lingkungan: str | None
    no_handphone: str | None = Field(alias="noHandphone")
    instagram: str | None
    birthday: date | None
    age: str | None
    status: str | None
    points: int                    # NEW
    total_score: int = Field(alias="totalScore")  # NEW

class MemberReadWithEvents(MemberRead):
    # embed events using the existing EventRead (which aliases starts_at -> "datetime")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    events: list[EventRead] = []

# ===== Points ops =====
class PointsAdjustInput(BaseModel):
    amount: int
    note: str | None = None

# ===== Change cardId =====
class RecardInput(BaseModel):
    new_card_id: str = Field(alias="newCardId")


# ===== Tap-in by cardId =====
class TapInInput(BaseModel):
    card_id: str = Field(alias="cardId")

class GradeInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    card_id: str = Field(alias="cardId")
    score: int
    notes: str | None = None

class EventWithGrade(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int
    title: str
    subtitle: str | None
    starts_at: datetime = Field(alias="datetime")
    status: str
    basic_point: int = Field(alias="basicPoint")
    score: int | None = None
    notes: str | None = None
    disiplin: int | None = None
    tanggung_jawab: int | None = Field(default=None, alias="tanggungJawab")
    percaya_diri: int | None = Field(default=None, alias="percayaDiri")
    keaktifan: int | None = None

class GradeAspectsInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    card_id: str = Field(alias="cardId")
    disiplin: int
    tanggung_jawab: int = Field(alias="tanggungJawab")
    percaya_diri: int = Field(alias="percayaDiri")
    keaktifan: int
    notes: str | None = None

class MemberInEventRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    # base member fields
    id: int
    card_id: str = Field(alias="cardId")
    name: str
    wilayah: str | None = None
    lingkungan: str | None = None
    no_handphone: str | None = Field(default=None, alias="noHandphone")
    instagram: str | None = None
    birthday: date | None = None
    age: str | None = None
    status: str
    points: int
    total_score: int = Field(alias="totalScore")

    # per-event grading
    score: int | None = None
    notes: str | None = None
    disiplin: int | None = None
    tanggung_jawab: int | None = Field(default=None, alias="tanggungJawab")
    percaya_diri: int | None = Field(default=None, alias="percayaDiri")
    keaktifan: int | None = None

    tapped_at: datetime | None = Field(default=None, alias="tappedAt")

class EventWithScore(EventRead):
    # from EventMemberLink
    score: int | None = None
    notes: str | None = None
    disiplin: int | None = None
    tanggung_jawab: int | None = Field(default=None, alias="tanggungJawab")
    percaya_diri: int | None = Field(default=None, alias="percayaDiri")
    keaktifan: int | None = None

    tapped_at: datetime | None = Field(default=None, alias="tappedAt")

class MemberDetailWithEvents(MemberRead):
    # list of events the member joined, each with grading info
    events: list[EventWithScore] = []