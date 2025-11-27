"""Mock LLM client by default. It *simulates* the LLM producing the
structured JSON (intent + slots + plan + natural_response) required by the
controller. These mocks are intentionally simple and deterministic so the app
can be tested locally without an external LLM.
"""

import re
import datetime
from typing import Dict, Any


def _next_weekday_date(weekday_name: str) -> str:
    today = datetime.date.today()
    weekday_list = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if weekday_name not in weekday_list:
        return None
    target = weekday_list.index(weekday_name)
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (today + datetime.timedelta(days=days_ahead)).isoformat()


def mock_parse_intent(text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Return a deterministic parse of user_text into the JSON contract.

    Output shape:
      {intent: str, slots: {...}, plan: [...], natural_response: str}
    """
    t = (text or "").strip()
    tl = t.lower()
    now = datetime.date.today()

    slots = {
        "date": None,
        "time": None,
        "party_size": None,
        "area": None,
        "preferences": None,
        "name": None,
        "contact": None,
        "booking_id": None,
    }

    intent = "unknown"
    plan = []

    # intent detection
    if any(w in tl for w in ["book", "reserve", "reservation", "table"]):
        intent = "book"
    elif any(w in tl for w in ["recommend", "suggest", "where should i"]):
        intent = "recommend"
    elif any(w in tl for w in ["cancel", "cancel booking", "i want to cancel"]):
        intent = "cancel"
    elif any(w in tl for w in ["change", "modify", "reschedule"]):
        intent = "modify"

    # date parsing
    if "today" in tl:
        slots["date"] = now.isoformat()
    elif "tomorrow" in tl:
        slots["date"] = (now + datetime.timedelta(days=1)).isoformat()
    else:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", tl)
        if m:
            slots["date"] = m.group(1)
        else:
            for wd in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                if wd in tl:
                    slots["date"] = _next_weekday_date(wd)
                    break

    # time parsing
    mtime = re.search(r"(\d{1,2}:\d{2})", tl)
    if mtime:
        slots["time"] = mtime.group(1)
    else:
        m2 = re.search(r"(\d{1,2})\s*(am|pm)", tl)
        if m2:
            h = int(m2.group(1))
            ampm = m2.group(2)
            if ampm == "pm" and h < 12:
                h += 12
            slots["time"] = f"{h:02d}:00"

    # party size
    mps = re.search(r"for (\d{1,2})", tl)
    if not mps:
        mps = re.search(r"party of (\d{1,2})", tl)
    if mps:
        slots["party_size"] = int(mps.group(1))

    # area heuristics
    known_areas = ["koramangala", "indiranagar", "mg road", "brigade road", "jayanagar", "whitefield", "hebbal", "majestic", "malleshwaram", "yelahanka", "ulsoor"]
    for a in known_areas:
        if a in tl:
            slots["area"] = a.title()
            break

    # booking id
    m_bid = re.search(r"(booking(?: id)?|id)\s*(#?)([0-9a-zA-Z_-]{3,})", tl)
    if m_bid:
        slots["booking_id"] = m_bid.group(3)

    # contact
    m_contact = re.search(r"(\+?\d[\d\-\s]{7,}\d)", text)
    if m_contact:
        slots["contact"] = m_contact.group(1)

    # Build plan based on intent
    if intent == "book":
        if slots["area"] and slots["party_size"]:
            plan = [{"action": "search_locations", "args": {"area": slots["area"], "party_size": slots["party_size"], "limit": 3}}]
        else:
            plan = []

    elif intent == "recommend":
        plan = [{"action": "search_locations", "args": {"area": slots.get("area") or "", "party_size": slots.get("party_size") or 2, "limit": 5}}]

    elif intent == "cancel":
        if slots.get("booking_id"):
            plan = [{"action": "cancel_reservation", "args": {"booking_id": slots.get("booking_id")}}]
        else:
            plan = []

    else:
        plan = []

    natural_response = ""
    if intent == "book":
        if not slots.get("date") or not slots.get("time"):
            natural_response = "What date and time would you like to book?"
        elif not slots.get("party_size"):
            natural_response = "How many people is the booking for?"
        else:
            natural_response = f"Searching for available restaurants in {slots.get('area', 'your area')} for {slots.get('party_size')} people on {slots.get('date')} at {slots.get('time')}."
    elif intent == "recommend":
        natural_response = f"Looking for recommendations in {slots.get('area', 'your area')} for {slots.get('party_size', 2)} people."
    elif intent == "cancel":
        natural_response = f"Attempting to cancel booking {slots.get('booking_id')}." if slots.get('booking_id') else "Please provide your booking ID to cancel."
    else:
        natural_response = "I can help you book, modify, cancel, or recommend restaurants. What would you like to do?"

    return {"intent": intent, "slots": slots, "plan": plan, "natural_response": natural_response}


def mock_format_response(original_text: str, tool_results: Dict[str, Any]) -> str:
    """Format tool results into a short natural language response for the user."""
    # booking confirmation
    if tool_results.get("create_reservation"):
        cr = tool_results.get("create_reservation")
        if cr.get("success"):
            return f"✅ Reservation confirmed! ID: {cr.get('id')}. {cr.get('restaurant_name')} on {cr.get('datetime')} for {cr.get('party_size')} people."
        return f"Could not create reservation: {cr.get('reason')}"

    if tool_results.get("search_locations") is not None:
        items = tool_results.get("search_locations") or []
        if not items:
            return "I couldn't find matching restaurants. Would you like to change area or time?"
        lines = [f"{i+1}. {r.get('name')} — {', '.join(r.get('cuisines', []))} — Rating {r.get('rating')}" for i, r in enumerate(items[:5])]
        return "Here are top options:\n" + "\n".join(lines)

    if tool_results.get("cancel_reservation"):
        cr = tool_results.get("cancel_reservation")
        if cr.get("success"):
            return f"✅ Booking {cr.get('id')} cancelled." 
        return "Unable to cancel the booking."

    return "OK"
