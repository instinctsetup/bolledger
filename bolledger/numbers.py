"""Parse amounts from Hinglish/Hindi speech: digits and Hindi number words.

Handles: "250", "250 rupaye", "do sau", "paanch sau", "ek hazaar",
"do hazaar paanch sau", "dedh sau" (150), "dhai hazaar" (2500), "sava lakh".
"""
import re

UNITS = {
    "ek": 1, "do": 2, "teen": 3, "tin": 3, "char": 4, "chaar": 4,
    "paanch": 5, "panch": 5, "chhe": 6, "chhah": 6, "che": 6, "saat": 7,
    "aath": 8, "ath": 8, "nau": 9, "nav": 9, "das": 10, "gyarah": 11,
    "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15, "solah": 16,
    "satrah": 17, "atharah": 18, "unnis": 19, "bees": 20,
    "tees": 30, "chalis": 40, "pachaas": 50, "saath": 60, "sattar": 70,
    "assi": 80, "assii": 80, "navve": 90, "nabbe": 90,
}
# "dedh/dhai/sava" = 1.5/2.5/1.25 of the FOLLOWING multiplier (dedh sau=150, dhai hazaar=2500);
# standalone they imply sau. adha/paune = 0.5/0.75 similarly.
SPECIAL_FACTOR = {"dedh": 1.5, "dhai": 2.5, "sava": 1.25, "adha": 0.5, "paune": 0.75}
MULTIPLIERS = {"sau": 100, "so": 100, "hazaar": 1000, "hazar": 1000,
               "hajjar": 1000, "lakh": 100000, "laakh": 100000, "crore": 10000000}

_TOKEN = re.compile(r"[a-z]+|\d+(?:\.\d+)?")


def parse_amount(text: str) -> tuple[float | None, str]:
    """Return (amount, evidence substring) for the first amount in text, else (None, '')."""
    m = re.search(r"\d+(?:\.\d+)?", text)
    if m:
        return float(m.group()), m.group()
    words = _TOKEN.findall(text.lower())
    segments, current, used = [], 0.0, []
    after_mult = False
    i = 0
    while i < len(words):
        w = words[i]
        if w in SPECIAL_FACTOR:
            if after_mult and current:
                segments.append(current)
                current = 0.0
            nxt = words[i + 1] if i + 1 < len(words) else None
            mult = MULTIPLIERS.get(nxt, 100)
            current += SPECIAL_FACTOR[w] * mult
            used.append(w)
            if nxt in MULTIPLIERS:
                used.append(nxt)
                i += 1
            after_mult = mult >= 1000
        elif w in UNITS:
            if after_mult and current:
                segments.append(current)   # "do hazaar" done, "paanch sau" starts fresh
                current = 0.0
            current += UNITS[w]; used.append(w)
            after_mult = False
        elif w in MULTIPLIERS:
            mult = MULTIPLIERS[w]
            if w in ("sau", "so") and current >= 100:
                pass  # "dedh sau": dedh already means 150, 'sau' is redundant
            else:
                current = max(1, current) * mult
            used.append(w)
            after_mult = mult >= 1000
        else:
            if used:
                break
        i += 1
    if current or segments:
        return float(sum(segments) + current), " ".join(used)
    return None, ""
