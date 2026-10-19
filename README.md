# bolledger

**बोली लिखो, बाकी अपने आप।** An offline, Hindi/Hinglish-first voice ledger for
small shopkeepers. Speak or type one line - "रमेश को पांच सौ उधार दिया" -
and bolledger turns it into a structured ledger entry, keeps running balances,
and closes the day with a one-line hisaab.

No paid API keys. No cloud dependency. Everything below runs locally on CPU.

- **Demo video**: https://drive.google.com/file/d/1XLysEDrtbzCxFv3BW_zwiYDuhaAOzH9g/view
- **Project report (PDF)**: https://drive.google.com/file/d/1SXhtNETpdFWCUg-5gODHl2b9dqJ8RX_p/view
- Repo: https://github.com/instinctsetup/bolledger

## What it does

| You say / type | bolledger does |
|---|---|
| "रमेश को पांच सौ उधार दिया" | credit entry ₹500 under Ramesh |
| "सुरेश ने 200 जमा किया" | payment received, balance updated |
| "आज 1500 की बिक्री हुई" | cash sale for the day |
| "बिजली का बिल 800" | expense entry |
| "रामेश का बैलेंस बताओ" | running balance for that customer |
| "आज का हिसाब दिखा" | day close: sales, receipts, new credit, expenses, net cash, total outstanding |

One-tap undo on every entry. CSV export. Everything stored in local SQLite.

## How it works

```
voice (Hindi) ──► faster-whisper (local STT)
                     │  Devanagari text
                     ▼
        transliterate.py ──► roman Hinglish
                     ▼
        HinglishNLU: pure-python multinomial Naive Bayes
        (word unigrams + char 3-5-grams, Laplace smoothing)
                     │  intent + name + amount (rule parser: dhai sau = 250)
                     ▼
        SQLite ledger (integer paise, derived balances)
                     ▼
        Hinglish reply + live UI update
```

- **STT**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper), CPU int8.
  `base` by default, `BOLLEDGER_WHISPER_MODEL=small` recommended. A Devanagari
  initial prompt keeps the decoder from drifting into Arabic-script Urdu.
- **NLU**: own model, no ML framework. Corpus: 2,460 template-generated
  Hinglish examples across 7 intents, plus a 30-sentence handwritten eval set.
- **Money**: integer paise everywhere; floats only for display. Balances are
  computed, so undo is a flag flip.

## Measured results

| eval | accuracy |
|---|---|
| template holdout (492, same distribution) | 0.9980 |
| handwritten set (30 sentences, not generated) | **30/30** intent, 20/20 amounts |
| voice round trip (synthetic Hindi TTS → entry) | verified end-to-end |

Reproduce: `python3 scripts/run_experiments.py`. Full tables, confusion matrix,
train-size curve: [docs/experiments.md](docs/experiments.md). Math and honest
limitations: [MATH.md](MATH.md). Viva prep: [VIVA.md](VIVA.md).

## Quickstart

```bash
pip install -r requirements.txt          # text mode needs only fastapi+uvicorn
python3 -m uvicorn server:app --port 8100
# open http://localhost:8100
```

Voice mode additionally needs `faster-whisper` (already in requirements); the
model downloads on first use. Docker: `docker build -t bolledger . && docker
run -p 8100:8100 bolledger`.

## Honest limitations

- The 0.998 holdout is same-distribution; the 30-sentence handwritten set is
  the honest generalization number and it is small. See MATH.md §6.
- STT quality on real noisy shop audio is untested - verified only with
  synthetic TTS audio (documented in MATH.md §6.2).
- Name extraction is lexical, not NER.
- Single-user, single-device. No auth, no sync.

## Tests

```bash
python3 -m pytest tests/ -q    # 34 tests: numbers, corpus, NLU, ledger, API, transliteration, Devanagari brain
```

CI runs the same suite on every push (.github/workflows/ci.yml).
