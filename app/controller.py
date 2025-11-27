"""Controller: receives `user_text`, calls LLM to parse intent, validates the
structured output, executes only whitelisted tools and returns a user-facing
reply plus debug information.

This controller uses the mock LLM client by default (for local testing). The
mock functions live in `app/llm_client.py` and return the exact JSON shape the
controller expects (intent, slots, plan, natural_response).
"""

from typing import Dict, Any, List
from app import llm_client, tools, recommender

# Allowed actions that the controller may execute
ALLOWED_ACTIONS = {
    "search_locations",
    "check_availability",
    "create_reservation",
    "modify_reservation",
    "cancel_reservation",
    "send_notification",
}


def validate_llm_output(llm_out: Dict[str, Any]) -> bool:
    """Validate that LLM output contains required top-level fields and that
    the plan only uses allowed actions."""
    if not isinstance(llm_out, dict):
        return False
    for k in ("intent", "slots", "plan", "natural_response"):
        if k not in llm_out:
            return False
    plan = llm_out.get("plan") or []
    if not isinstance(plan, list):
        return False
    for step in plan:
        if not isinstance(step, dict):
            return False
        if step.get("action") not in ALLOWED_ACTIONS:
            return False
    return True


def _execute_step(step: Dict[str, Any], slots: Dict[str, Any]) -> Any:
    action = step.get("action")
    args = step.get("args", {}) or {}
    if action == "search_locations":
        area = args.get("area", "")
        party_size = int(args.get("party_size", slots.get("party_size", 2) or 2))
        limit = int(args.get("limit", 3))
        items = tools.search_locations(area=area, party_size=party_size, limit=limit)
        items = recommender.recommend(items, party_size=party_size, limit=limit)
        return items

    if action == "check_availability":
        return tools.check_availability(args.get("restaurant_id"), args.get("datetime"), int(args.get("party_size", slots.get("party_size", 2) or 2)))

    if action == "create_reservation":
        return tools.create_reservation(
            args.get("restaurant_id"),
            args.get("restaurant_name", "Unknown"),
            args.get("datetime"),
            int(args.get("party_size", slots.get("party_size", 2) or 2)),
            args.get("name") or slots.get("name") or "Guest",
            args.get("contact") or slots.get("contact") or "N/A",
        )

    if action == "modify_reservation":
        return tools.modify_reservation(args.get("booking_id"), args.get("new_datetime"), args.get("new_party_size"))

    if action == "cancel_reservation":
        return tools.cancel_reservation(args.get("booking_id"))

    if action == "send_notification":
        return tools.send_notification(args.get("method", "sms"), args.get("dest"), args.get("message", ""))

    return {"error": "UNSUPPORTED_ACTION"}


def execute_plan(plan: List[Dict[str, Any]], slots: Dict[str, Any]) -> Dict[str, Any]:
    results = {}
    for step in plan:
        action = step.get("action")
        # safety: only execute allowed actions
        if action not in ALLOWED_ACTIONS:
            results[action] = {"error": "NOT_ALLOWED"}
            continue
        try:
            results[action] = _execute_step(step, slots)
        except Exception as e:
            results[action] = {"error": "EXCEPTION", "reason": str(e)}
    return results


def handle_message(user_text: str, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Primary entrypoint for the Streamlit app.

    Returns:
      {"success": bool, "reply": str, "debug": {...}}
    """
    try:
        # Parse with mock or real LLM function
        parser = getattr(llm_client, "mock_parse_intent", None) or getattr(llm_client, "parse_intent")
        llm_out = parser(user_text, context=session_context)
    except Exception as e:
        return {"success": False, "reply": "Internal error parsing your message.", "debug": {"error": str(e)}}

    if not validate_llm_output(llm_out):
        return {"success": False, "reply": "Sorry, I couldn't understand that. Can you rephrase?", "debug": llm_out}

    plan = llm_out.get("plan", []) or []
    slots = llm_out.get("slots", {}) or {}

    # If plan missing but intent=book and basic slots present, add a search
    if not plan and llm_out.get("intent") == "book" and slots.get("area") and slots.get("party_size"):
        plan = [{"action": "search_locations", "args": {"area": slots.get("area"), "party_size": slots.get("party_size"), "limit": 3}}]

    # Execute plan
    tool_results = execute_plan(plan, slots)

    # Post-processing: if booking intent and we have results + date/time, try auto-create
    reply = None
    try:
        if llm_out.get("intent") == "book":
            if tool_results.get("search_locations") and slots.get("date") and slots.get("time"):
                items = tool_results.get("search_locations")
                if items:
                    top = items[0]
                    # Normalize datetime -> ISO
                    datetime_iso = f"{slots['date']}T{slots['time']}"
                    cr = tools.create_reservation(top.get("id"), top.get("name"), datetime_iso, int(slots.get("party_size", 2)), slots.get("name"), slots.get("contact"))
                    tool_results["create_reservation"] = cr
                    reply = llm_client.mock_format_response(user_text, tool_results)
                else:
                    reply = "No matching restaurants found. Would you like a nearby area or different time?"
            else:
                reply = llm_client.mock_format_response(user_text, tool_results)
        else:
            reply = llm_client.mock_format_response(user_text, tool_results)
    except Exception as e:
        return {"success": False, "reply": "Error executing tools.", "debug": {"exception": str(e), "llm_out": llm_out, "tool_results": tool_results}}

    return {"success": True, "reply": reply or "OK", "debug": {"llm_out": llm_out, "tool_results": tool_results}}
