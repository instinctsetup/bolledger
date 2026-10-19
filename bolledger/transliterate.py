"""Devanagari -> roman transliteration for the NLU input path.

Deterministic letter mapping with approximate schwa deletion:
- consonant + vowel sign  -> consonant + vowel
- consonant + halant      -> consonant
- bare consonant          -> consonant + 'a', except at word end (schwa dropped)
- anusvara                 -> 'n'

It is deliberately simple (not IAST); it targets the vocabulary shopkeepers
actually say. The NLU's char n-gram features tolerate the remaining variance.
"""

CONS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
    "ळ": "l", "क्ष": "ksh", "ज्ञ": "gy",
}
VOWELS_INDEP = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
                "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऋ": "ri"}
VOWELS_DEP = {"ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
              "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ृ": "ri"}
HALANT = "्"
ANUSVARA = "ं"
NUKTA = "़"
DEV_DIGITS = {"०": "0", "१": "1", "२": "2", "३": "3", "४": "4", "५": "5", "६": "6", "७": "7", "८": "8", "९": "9"}


def has_devanagari(text: str) -> bool:
    return any("ऀ" <= c <= "ॿ" for c in text)


def transliterate_word(word: str) -> str:
    out: list[str] = []
    chars = list(word)
    i = 0
    while i < len(chars):
        c = chars[i]
        if c in DEV_DIGITS:
            out.append(DEV_DIGITS[c]); i += 1; continue
        if c in VOWELS_INDEP:
            out.append(VOWELS_INDEP[c]); i += 1; continue
        if c in CONS:
            base = CONS[c]
            nxt = chars[i + 1] if i + 1 < len(chars) else None
            if nxt == HALANT:
                out.append(base); i += 2; continue
            if nxt == NUKTA:  # e.g. क़ -> k (nukta ignored, close enough for NLU)
                out.append(base); i += 2
                if i < len(chars) and chars[i] == HALANT:
                    i += 1
                continue
            if nxt in VOWELS_DEP:
                out.append(base + VOWELS_DEP[nxt]); i += 2; continue
            if nxt == ANUSVARA:
                out.append(base + "an"); i += 2; continue
            # bare consonant: inherent 'a', dropped at word end (approximate schwa deletion)
            out.append(base + ("a" if i < len(chars) - 1 else ""))
            i += 1; continue
        if c == ANUSVARA:
            out.append("n"); i += 1; continue
        out.append(c); i += 1
    return "".join(out)


# number words whose natural transliteration differs from the parser's spelling
NUMBER_WORDS = {"dhaaee": "dhai", "savaa": "sava", "dhaai": "dhai"}


def to_roman(text: str) -> str:
    """Transliterate a Devanagari (or mixed) string to lowercase roman."""
    words = text.split()
    out = []
    for w in words:
        w2 = "".join(DEV_DIGITS.get(c, c) for c in w)
        roman = transliterate_word(w2) if has_devanagari(w2) else w2.lower()
        out.append(NUMBER_WORDS.get(roman, roman))
    return " ".join(out)
