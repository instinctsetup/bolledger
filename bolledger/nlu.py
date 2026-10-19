"""Hinglish NLU: intent classification (multinomial Naive Bayes on word+char n-grams,
pure numpy) + entity extraction (customer name, amount, item).

No paid APIs, no external models - the classifier trains in milliseconds on our
own corpus and serializes to JSON.
"""
import json
import math
import re
from collections import Counter, defaultdict
from .numbers import parse_amount

_WORD = re.compile(r"[a-z]+|\d+")
STOP = {"ko", "ne", "ka", "ki", "ke", "se", "mein", "hai", "hua", "aaj", "rupaye", "lo", "de", "diya"}

INTENT_LABELS = ["udhaar_diya", "jama", "bikri", "kharcha", "balance_query", "hisaab", "unknown"]


def tokenize(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def features(tokens: list[str]) -> list[str]:
    """Word unigrams + bigrams + char 3-gram prefixes for morphology ("diya"/"diye")."""
    feats = [f"w:{t}" for t in tokens]
    feats += [f"b:{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
    for t in tokens:
        if len(t) > 3:
            feats.append(f"c:{t[:4]}")
    return feats


class NaiveBayes:
    """Multinomial NB with Laplace smoothing. Pure python + dicts (tiny data)."""

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.class_doc_counts: Counter = Counter()
        self.feature_counts: dict[str, Counter] = defaultdict(Counter)
        self.class_totals: Counter = Counter()
        self.vocab: set[str] = set()

    def fit(self, data: list[tuple[str, str]]) -> "NaiveBayes":
        for text, label in data:
            self.class_doc_counts[label] += 1
            for f in features(tokenize(text)):
                self.feature_counts[label][f] += 1
                self.class_totals[label] += 1
                self.vocab.add(f)
        return self

    def _log_prob(self, feats: list[str], label: str) -> float:
        n_classes = len(self.class_doc_counts)
        prior = math.log((self.class_doc_counts[label] + 1) / (sum(self.class_doc_counts.values()) + n_classes))
        denom = self.class_totals[label] + self.alpha * len(self.vocab)
        lp = prior
        for f in feats:
            lp += math.log((self.feature_counts[label][f] + self.alpha) / denom)
        return lp

    def predict_proba(self, text: str) -> dict[str, float]:
        feats = features(tokenize(text))
        if not self.class_doc_counts:
            return {}
        logs = {c: self._log_prob(feats, c) for c in self.class_doc_counts}
        mx = max(logs.values())
        exps = {c: math.exp(v - mx) for c, v in logs.items()}
        total = sum(exps.values())
        return {c: v / total for c, v in exps.items()}

    def predict(self, text: str) -> tuple[str, float]:
        probs = self.predict_proba(text)
        if not probs:
            return "unknown", 0.0
        best = max(probs, key=probs.get)
        return best, probs[best]

    def to_json(self) -> dict:
        return {
            "alpha": self.alpha,
            "class_doc_counts": dict(self.class_doc_counts),
            "feature_counts": {c: dict(fc) for c, fc in self.feature_counts.items()},
            "class_totals": dict(self.class_totals),
            "vocab": sorted(self.vocab),
        }

    @classmethod
    def from_json(cls, d: dict) -> "NaiveBayes":
        nb = cls(alpha=d["alpha"])
        nb.class_doc_counts = Counter(d["class_doc_counts"])
        nb.feature_counts = defaultdict(Counter, {c: Counter(fc) for c, fc in d["feature_counts"].items()})
        nb.class_totals = Counter(d["class_totals"])
        nb.vocab = set(d["vocab"])
        return nb


# Known shopkeeper names get a boost, but any capitalized/unknown word after
# "ko"/"ne" patterns is accepted as a name.
_KNOWN_NAMES = {"ramesh", "suresh", "mahesh", "dinesh", "raju", "karan", "imran", "salman",
                "vijay", "ajay", "sunita", "geeta", "rekha", "farhan", "mohan"}


def _collapse_doubles(w: str) -> str:
    """'raamesh' -> 'ramesh'; used only for name matching, not features."""
    out = []
    for c in w:
        if not out or out[-1] != c:
            out.append(c)
    return "".join(out)


def extract_name(text: str) -> str | None:
    """Customer name: known name, or the word right before ko/ne/ka/kaa/se.

    Transliterated Devanagari produces double vowels ('raamesh') and long
    particles ('kaa'), so matching collapses doubled letters.
    """
    toks = tokenize(text)
    collapsed = {_collapse_doubles(t) for t in _KNOWN_NAMES}
    for t in toks:
        if _collapse_doubles(t) in collapsed:
            return _collapse_doubles(t).capitalize()
    for i, t in enumerate(toks[:-1]):
        if toks[i + 1] in ("ko", "ne", "ka", "kaa", "se") and t not in STOP and not t.isdigit():
            return _collapse_doubles(t).capitalize()
    return None


def extract_item(text: str) -> str | None:
    toks = tokenize(text)
    for t in toks:
        if t in {"cheeni", "atta", "chawal", "tel", "sabun", "biscuit", "namkeen", "daal", "masala", "doodh", "paneer", "sabzi"}:
            return t
    return None


class HinglishNLU:
    def __init__(self, model: NaiveBayes | None = None, threshold: float = 0.35):
        self.model = model or NaiveBayes()
        self.threshold = threshold  # below this confidence, answer "unknown"

    def train(self, data: list[tuple[str, str]]) -> "HinglishNLU":
        self.model.fit(data)
        return self

    def parse(self, text: str) -> dict:
        intent, conf = self.model.predict(text)
        if conf < self.threshold:
            intent = "unknown"
        amount, evidence = parse_amount(text)
        # names only make sense for person-centric intents
        name = extract_name(text) if intent in ("udhaar_diya", "jama", "balance_query") else None
        return {
            "text": text,
            "intent": intent,
            "confidence": round(conf, 3),
            "amount": amount,
            "amount_evidence": evidence,
            "name": name,
            "item": extract_item(text),
        }

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.model.to_json(), f)

    @classmethod
    def load(cls, path: str) -> "HinglishNLU":
        with open(path) as f:
            return cls(NaiveBayes.from_json(json.load(f)))
