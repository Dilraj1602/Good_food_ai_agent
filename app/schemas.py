from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SlotSet(BaseModel):
    date: Optional[str] = None   # YYYY-MM-DD
    time: Optional[str] = None   # HH:MM (24h)
    party_size: Optional[int] = None
    area: Optional[str] = None
    preferences: Optional[str] = None
    name: Optional[str] = None
    contact: Optional[str] = None
    booking_id: Optional[str] = None

class Action(BaseModel):
    action: str
    args: Dict[str, Any] = {}

class LLMOutput(BaseModel):
    intent: str
    slots: SlotSet
    plan: List[Action] = []
    natural_response: str

class Reservation(BaseModel):
    id: str
    restaurant_id: str
    datetime: str
    party_size: int
    name: str
    contact: str
    status: str = "CONFIRMED"
    created_at: str = None
