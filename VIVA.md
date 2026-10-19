# VIVA.md - likely questions and straight answers

**Why Naive Bayes instead of an LLM or a fine-tuned transformer?**
Cost and constraint. The app must run fully offline on cheap hardware with zero
API keys. NB trains in <1s on CPU, infers in microseconds, ships as auditable
JSON, and hits 30/30 on our handwritten eval. An LLM would be better on
open-world phrasing and worse on every constraint that matters here.

**Your holdout accuracy is 0.998 - is that real?**
It's real but narrow: train and test come from the same template families, so it
measures interpolation, not generalization. The honest generalization number is
the 30/30 handwritten set, which is small. We show the confusion matrix and
train-size curve in docs/experiments.md and say all of this in MATH.md §6.

**Why integer paise?**
Binary floats can't represent 0.1. Summed over thousands of ledger rows that
error becomes visible money. Integer paise sums are exact; floats exist only at
the display boundary.

**How does "dhai sau" become 250?**
dhai/dedh/sava are factors of the following multiplier, not constants:
dhai sau = 2.5×100 = 250; dedh hazaar = 1.5×1000 = 1500. Standalone "dhai"
without a multiplier is 2.5. 25 unit tests pin the grammar.

**Why transliterate instead of training on Devanagari?**
One model serving both scripts. Transliteration is deterministic, so the corpus
only has to cover one spelling family (plus the transliterator's quirks, which
we measured and added as training variants). Training a second Devanagari model
doubles the corpus for no accuracy gain on this size.

**Why does STT need an initial prompt?**
Whisper base, given Hindi audio from a synthetic TTS voice, sometimes outputs
Arabic-script Urdu. A Devanagari initial prompt biases the decoder to
Devanagari. This is a known whisper behavior; we hit it, measured it, and
documented the fix.

**What breaks first in production?**
Noise. A shop floor is not TTS audio. The VAD filter helps, but far-field mic
noise on a phone will hurt word error rate, and every STT error compounds into
NLU. Mitigation path: show the transcript and make undo one tap (we do), and let
the user correct by typing (we do).

**What's the DB schema?**
customers(id, name), transactions(id, ts, kind, paise, customer_id?, note,
raw_text, confidence, undone). Balances are computed views, never stored, so
undo is just a flag flip - no balance repair needed.
