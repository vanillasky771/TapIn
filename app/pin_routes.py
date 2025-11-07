import random
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from app.database import get_db
from app.models import Pin

router = APIRouter(prefix="/pin", tags=["PIN"])


def generate_pin_code() -> str:
    """Generate a 4-digit numeric PIN."""
    return f"{random.randint(0, 9999):04d}"


@router.post("/generate")
def generate_pin(name: str, db: Session = Depends(get_db)):
    """
    Generate a permanent 4-digit numeric PIN for the given name.
    If the name already has one, return the existing pin instead of creating a new one.
    """
    existing_pin = db.exec(select(Pin).where(Pin.name == name)).first()
    if existing_pin:
        return {
            "id": existing_pin.id,
            "name": existing_pin.name,
            "pin": existing_pin.pin,
            "message": "PIN already exists"
        }

    pin_value = generate_pin_code()
    pin_row = Pin(name=name, pin=pin_value)

    db.add(pin_row)
    db.commit()
    db.refresh(pin_row)

    return {
        "id": pin_row.id,
        "name": pin_row.name,
        "pin": pin_row.pin,
        "message": "New PIN generated"
    }

class PinVerifyRequest(BaseModel):
    pin: str

@router.post("/verify")
def verify_pin(data: PinVerifyRequest, db: Session = Depends(get_db)):
    record = db.exec(select(Pin).where(Pin.pin == data.pin)).first()
    if not record:
        raise HTTPException(status_code=404, detail="Invalid or unknown PIN")

    return {
        "status": "verified",
        "id": record.id,
        "name": record.name,
        "pin": record.pin,
    }


def must_get_valid_pin(pin: str, db: Session) -> Pin:
    """Helper to find a pin by code (no expiry validation)."""
    record = db.exec(select(Pin).where(Pin.pin == pin)).first()
    if not record:
        raise HTTPException(status_code=404, detail="PIN not found")
    return record
