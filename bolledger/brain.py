"""Glue: NLU parse -> ledger action -> Hinglish reply."""
from .nlu import HinglishNLU
from .ledger import Ledger
from .transliterate import has_devanagari, to_roman

RESP = {
    "udhaar_diya": "{name} ka ₹{amt:.0f} udhaar likh diya. Ab total udhaar ₹{bal:.0f}.",
    "jama": "{name} se ₹{amt:.0f} jama. Ab baaki ₹{bal:.0f}.",
    "bikri": "₹{amt:.0f} ki bikri likh di.",
    "kharcha": "₹{amt:.0f} ka kharcha likh diya.",
}


def handle_text(text: str, nlu: HinglishNLU, ledger: Ledger) -> dict:
    """Parse one utterance and apply it. Returns {parse, reply, action?, hisaab?}."""
    roman = to_roman(text) if has_devanagari(text) else text
    p = nlu.parse(roman)
    if roman != text:
        p["roman"] = roman
    intent, amt, name = p["intent"], p["amount"], p["name"]

    if intent in ("udhaar_diya", "jama"):
        if amt is None:
            return {"parse": p, "reply": "Kitne rupaye? Amount samajh nahi aaya - dobara boliye."}
        if not name:
            return {"parse": p, "reply": "Kiske naam? Grahak ka naam boliye."}
        tx = ledger.add(intent, amt, name, raw_text=text, confidence=p["confidence"])
        bal = ledger.balance(name)
        return {"parse": p, "reply": RESP[intent].format(name=name, amt=amt, bal=bal), "action": tx}

    if intent in ("bikri", "kharcha"):
        if amt is None:
            return {"parse": p, "reply": "Kitne ki? Amount dobara boliye."}
        note = p["item"] or ""
        tx = ledger.add(intent, amt, None, note=note, raw_text=text, confidence=p["confidence"])
        return {"parse": p, "reply": RESP[intent].format(amt=amt), "action": tx}

    if intent == "balance_query":
        if not name:
            return {"parse": p, "reply": f"Kiska balance? Total dukaan pe ₹{ledger.total_outstanding():.0f} udhaar chal raha hai."}
        bal = ledger.balance(name)
        if bal > 0:
            reply = f"{name} ka ₹{bal:.0f} baaki hai."
        elif bal < 0:
            reply = f"{name} ne ₹{-bal:.0f} zyada de diye hain (advance)."
        else:
            reply = f"{name} ka koi baaki nahi hai. Sab clear."
        return {"parse": p, "reply": reply}

    if intent == "hisaab":
        h = ledger.hisaab()
        reply = (f"Aaj ka hisaab: bikri ₹{h['bikri']:.0f} ({h['bikri_count']} entry), "
                 f"jama ₹{h['jama']:.0f}, naya udhaar ₹{h['udhaar_diya']:.0f}, "
                 f"kharcha ₹{h['kharcha']:.0f}. Cash mein net ₹{h['net_cash']:.0f}. "
                 f"Total udhaar baaki: ₹{h['total_outstanding']:.0f}.")
        return {"parse": p, "reply": reply, "hisaab": h}

    return {"parse": p, "reply": "Samajh nahi aaya. Boliye jaise: 'Ramesh ko 500 udhaar diya' ya 'aaj ka hisaab'."}
