# MATH.md - bolledger

The math behind each piece, with honest notes on what is measured and what is not.

## 1. Intent classification: multinomial Naive Bayes

Model: pure-Python multinomial NB over word unigrams + character n-grams (3-5).

For intent class c and utterance x with feature counts f_i:

    P(c | x)  ∝  P(c) · Π_i P(i | c)^f_i
    P(i | c)  =  (count(i, c) + α) / (total_tokens(c) + α·|V|),   α = 0.5 (Lidstone)

We work in log space: score(c) = log P(c) + Σ_i f_i · log P(i | c), then softmax
for a normalized confidence. If max_c P(c|x) < 0.35 the intent is set to `unknown`
and the app asks the user to repeat instead of guessing.

Why NB and not a neural model:
- The corpus is small (2,460 template-generated examples + 30 handwritten).
- Training must run offline on a shopkeeper's phone-class CPU in milliseconds.
- NB is exactly reproducible (no GPU nondeterminism) and the model serializes to
  plain JSON, so the saved model is auditable.

Char n-grams matter because Hinglish spelling is unstable: "bikri/bikree",
"batao/bataao", "balance/bailens". They also absorb the deterministic
transliteration quirks from the Devanagari path (see §4).

## 2. Hinglish amount parsing

`bolledger/numbers.py` is a rule parser, not ML, because amounts are money and a
learned parser can be confidently wrong.

    amount = Σ over detected (factor × multiplier) groups + stray digits

- multipliers: sau/hundred (100), hazaar/thousand (1000), lakh (100000)
- unit words: ek..nineteen, bees..ninety, and the fractions
- dhai = 2.5, dedh = 1.5, sava = 1.25 are **factors of the following
  multiplier**, never standalone: "dhai sau" = 2.5×100 = 250, "dedh hazaar" =
  1.5×1000 = 1500. (An earlier bug treated them as flat constants; 25 tests now
  pin this down.)
- Devanagari digits (५००) and Devanagari number words (पांच सौ) reach the same
  parser via the transliteration layer.

## 3. Money representation: integer paise

All ledger math is integer paise (1₹ = 100 paise) in SQLite. Floats appear only
at the API boundary for display. Rationale: binary floating point cannot
represent 0.1 exactly; summing thousands of float rupees accumulates error,
summing paise never does. Balances are derived, not stored:

    balance(customer) = Σ udhaar_diya − Σ jama        (per customer)
    net_cash(day)     = bikri + jama − kharcha
    total_outstanding = Σ positive customer balances

## 4. Devanagari → roman transliteration

Deterministic letter mapping with approximate schwa deletion:

- consonant + vowel sign → consonant + vowel
- consonant + halant → consonant
- bare consonant → consonant + 'a', except word-final (schwa dropped)
- anusvara ं → 'n'

This is a heuristic, not ISO 15919. Real schwa deletion is phonological
("रमेश"→ramesh but "सुरेश"→suresh both work; edge cases like consonant clusters
can over- or under-delete). We accept the noise because the NB's char n-grams
tolerate it, and we added transliteration-spelling variants to the corpus
("bikree", "kee", "bataao", "bailens") so the feature distribution matches what
the transliterator actually emits. Number words that diverge ("dhaaee"→"dhai")
are normalized by dictionary.

## 5. Measured results (reproduce: `python3 scripts/run_experiments.py`)

- corpus: 2,460 template-generated examples, 7 intents
- template holdout (80/20, fixed seed): **0.9980** intent accuracy
- handwritten eval set (30 sentences written by hand, not generated):
  **30/30** intent, **20/20** amounts on the items that carry amounts
- train-size curve: 0.9736 @196 examples → 0.9980 @1574

Full per-class precision/recall, confusion matrix and curve: `docs/experiments.md`.

## 6. Honest limitations

1. **Distribution gap.** The 0.998 holdout is on template-family data; real
   shopkeeper speech is noisier. The 30-sentence handwritten set is the more
   honest number but it is small. We report both, we do not blend them.
2. **STT on synthetic audio.** Verified end-to-end with piper Hindi TTS →
   faster-whisper: base model mangled synthetic speech ("पांच सौ उधार"→
   "पांच सोदार"); `small` fixed most of it but still dropped उ ("दार"), which
   the corpus now tolerates via documented STT-error variants. Without a
   Devanagari-biased initial prompt the base model sometimes emits
   Arabic-script Urdu for Hindi audio; the prompt pins the script.
3. **Name extraction is lexical** (ko/se/ka patterns + capitalization), not NER.
   Names that collide with intent words will misparse.
4. **Single-ledger, single-user.** No auth, no multi-device sync - out of scope
   for an offline-first demo.
