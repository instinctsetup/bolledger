"""Hinglish corpus for the ledger NLU: hand-written seeds + template expansion.

Intents:
  udhaar_diya   - credit given to a customer ("Ramesh ko 500 udhaar diya")
  jama          - payment received ("Suresh ne 200 jama kiya", "200 wapas aaya")
  bikri         - a sale ("aaj 300 ki bikri", "do kilo cheeni bechi 90 mein")
  kharcha       - shop expense ("bijli ka bill 800", "rent 5000 diya")
  balance_query - ask a customer's balance ("Ramesh ka kitna baaki hai")
  hisaab        - daily/weekly report ("aaj ka hisaab dikha")
  unknown       - anything else

Every example is (text, intent). Template expansion keeps grammar natural by
varying verbs, pronouns, amount placement and name position. The corpus is
synthetic-by-construction - README and MATH.md say so honestly.
"""
import itertools
import random

NAMES = ["ramesh", "suresh", "mahesh", "dinesh", "raju", "karan", "imran",
         "salman", "vijay", "ajay", "sunita", "geeta", "rekha", "farhan", "mohan"]
NAME_FORMS = NAMES + [f"{n} bhai" for n in NAMES] + [f"{n} ji" for n in NAMES]
AMOUNTS = ["50", "100", "150", "200", "250", "300", "500", "750", "1000",
           "do sau", "paanch sau", "ek hazaar", "dedh sau", "dhai hazaar",
           "teen sau", "saade paanch sau", "do hazaar"]
ITEMS = ["cheeni", "atta", "chawal", "tel", "sabun", "biscuit", "namkeen",
         "daal", "masala", "doodh", "paneer", "sabzi"]

UDHAAR_T = [
    "{name} ko {amt} udhaar de aaya", "{name} ne {amt} le liye udhaar pe",
    "{name} ka {amt} udhaar", "{name} ko {amt} udhaar likh do",
    "aaj {name} ne {amt} le liye udhaar pe", "{name} ko {amt} ka maal udhaar diya",
    "{name} ko {amt} udhaar diya", "{name} ko udhaar diya {amt}",
    "{amt} rupaye udhaar {name} ko", "{name} ko {amt} ka udhaar",
    "udhaar diya {name} ko {amt}", "{name} ne {amt} udhaar liya",
    "{name} ko {amt} dena hai udhaar", "{name} ka {amt} udhaar likho",
    "{name} ko {amt} udhaar de diya aaj", "likh lo {name} ko {amt} udhaar",
    # Whisper-STT error variants seen on synthetic TTS audio (documented in MATH.md):
    "{name} ko {amt} daar diya", "{name} ko {amt} daar diya aaj", "{amt} daar {name} ko",
]
JAMA_T = [
    "{name} {amt} wapas de gaya", "{name} se {amt} mil gaye",
    "{name} ne apna {amt} chuka diya", "{name} ka {amt} aa gaya",
    "{name} ne {amt} jama kar diye", "{name} ne {amt} wapas kar diya",
    "{name} ne {amt} jama kiya", "{name} ne {amt} diye", "{amt} jama hua {name} se",
    "{name} ka {amt} wapas aaya", "{name} ne udhaar ka {amt} diya",
    "{amt} mila {name} se", "{name} ne {amt} chuka diya",
    "{name} se {amt} aaya", "{name} ka {amt} jama likho", "{name} ne {amt} de diya",
]
BIKRI_T = [
    "subah se {amt} ki bikri ho gayi", "aaj {amt} ka maal gaya",
    "sale achhi thi aaj {amt} hui", "{item} ke packet {amt} ke bike",
    "aaj {amt} ki sale ho gayi", "{amt} ka {item} becha aaj",
    "maal gaya {amt} ka", "{item} {amt} ke bike aaj",
    "aaj {amt} ki bikri", "{amt} ka samaan becha", "{item} bechi {amt} mein",
    "bikri hui {amt} ki", "{amt} ki sale aaj", "{item} ka packet {amt} mein gaya",
    "aaj {amt} ka saamaan gaya", "{amt} rupaye ki bikri hui",
    "{item} {amt} mein becha", "sale {amt} aaj subah",
    # Devanagari-transliteration variants:
    "aaj {amt} kee bikree huee", "{amt} kee bikree huee aaj", "bikree huee {amt} kee",
    "aaj {amt} kee sale huee", "{amt} kaa samaan bechaa",
]
KHARCHA_T = [
    "bijli bill {amt} bhara", "aaj transport pe {amt} ud gaya",
    "dukaan ke liye samaan laya {amt} ka", "rent dena tha {amt} de diya",
    "safai wale ko {amt} diya", "{amt} ud gaya aaj kharch mein",
    "aaj {amt} ka kharcha ho gaya", "bill {amt} ka aaya tha diya",
    "bijli ka bill {amt}", "rent {amt} diya", "{amt} ka kharcha aaj",
    "kharcha {amt} dukan ka", "{amt} samaan laane mein kharch",
    "transport ka {amt} gaya", "{amt} bill bhara", "dukaan ka kharcha {amt}",
    "{amt} maintenance mein laga", "aaj kharcha hua {amt}",
    # Devanagari-transliteration variants (see bolledger/transliterate.py):
    "bijalee ka bil {amt}", "bijalee bil {amt} bharaa", "bil {amt} kaa aayaa",
    "aaj {amt} kaa kharcha ho gayaa", "rent {amt} diyaa", "kharcha {amt} dukaan kaa",
]
BALANCE_T = [
    "{name} ka total kitna hua ab tak", "{name} pe kitna udhaar chal raha hai",
    "{name} ka balance check karo", "{name} ko kitna dena baki hai",
    "{name} ka kitna baaki hai", "{name} ka balance batao", "{name} pe kitna udhaar hai",
    "kitna dena hai {name} ko", "{name} ka hisaab batao", "{name} ka kitna paisa baaki",
    "balance kya hai {name} ka", "{name} ka udhaar kitna hai",
    "{name} kaa balance bataao", "{name} kaa kitna baaki hai", "balance bataao {name} kaa",
    "{name} kaa bailens bataao", "bailens bataao {name} kaa", "{name} kaa kitnaa baaki hai",
]
HISAAB_T = [
    "aaj ka hisaab dikha", "aaj ka report", "kitna hua aaj", "aaj ka total batao",
    "hafte ka hisaab", "hisab dikhao", "aaj ka len den batao",
    "aaj kitna kamaya", "din ka len den batao", "aaj ka pura hisaab dikhao",
    "report dikhao", "hisaab batao aaj ka", "aaj ka collection kitna hua",
    "aaj kitna jama hua total", "aaj ka kharcha kitna hua", "aaj ka summary",
    "din bhar ka hisaab", "aaj dukaan ka hisaab", "total batao aaj ka",
    "aaj sab kitna hua", "summary dikhao aaj ki", "aaj ka balance sheet",
    "aaj ka hisaab kitab", "pura din ka report", "aaj ka status batao",
    "aaj kitna udhaar diya total", "hafte ka report dikhao", "aaj ka aankda",
]
UNKNOWN_T = [
    "kaise ho", "mausam kaisa hai", "cricket score kya hai", "namaste",
    "gaana bajao", "time kya hua", "shukriya", "ok theek hai",
    "kal chutti hai", "phone kahan rakha", "hello bhaiya",
    "kal dukaan band rahegi", "bahut garmi hai aaj", "kya chal raha hai",
    "aaj bahut bheed hai", "aaj toh neend aa rahi hai", "aaj match hai",
    "aaj chhutti manani hai", "aaj mausam accha hai", "aaj bahut thak gaya",
    "kya haal hai", "sab badhiya", "dhaabe pe chalte hain", "chai piyoge",
]


def expand(templates: list[str], names: list[str], amounts: list[str], items: list[str],
           cap: int = 500, seed: int = 11) -> list[str]:
    """Expand templates over slot values, SAMPLED so every template contributes
    (sequential truncation would starve templates later in the list)."""
    rng = random.Random(seed)
    all_combos: list[str] = []
    for t in templates:
        slots = {
            "name": names if "{name}" in t else [""],
            "amt": amounts if "{amt}" in t else [""],
            "item": items if "{item}" in t else [""],
        }
        for combo in itertools.product(slots["name"], slots["amt"], slots["item"]):
            all_combos.append(t.format(name=combo[0], amt=combo[1], item=combo[2]).strip())
    rng.shuffle(all_combos)
    return all_combos[:cap]


def build_corpus(seed: int = 42) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    corpus: list[tuple[str, str]] = []
    for templates, intent in [(UDHAAR_T, "udhaar_diya"), (JAMA_T, "jama"), (BIKRI_T, "bikri"),
                              (KHARCHA_T, "kharcha"), (BALANCE_T, "balance_query"),
                              (HISAAB_T, "hisaab")]:
        for text in expand(templates, NAME_FORMS, AMOUNTS, ITEMS):
            corpus.append((text, intent))
    corpus += [(t, "unknown") for t in UNKNOWN_T]
    rng.shuffle(corpus)
    return corpus


def train_test_split(corpus: list[tuple[str, str]], frac_train: float = 0.8, seed: int = 7):
    rng = random.Random(seed)
    data = corpus[:]
    rng.shuffle(data)
    cut = int(len(data) * frac_train)
    return data[:cut], data[cut:]
