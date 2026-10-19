import json
from pathlib import Path
from bolledger.corpus import build_corpus, train_test_split
from bolledger.nlu import HinglishNLU, NaiveBayes

def _trained():
    train, _ = train_test_split(build_corpus())
    return HinglishNLU().train(train)

def test_intents_basic():
    nlu = _trained()
    cases = {
        "ramesh ko 500 udhaar diya": "udhaar_diya",
        "suresh ne 200 jama kiya": "jama",
        "aaj 1200 ki bikri": "bikri",
        "bijli ka bill 800": "kharcha",
        "ramesh ka kitna baaki hai": "balance_query",
        "aaj ka hisaab dikha": "hisaab",
        "cricket score kya hai": "unknown",
    }
    for text, want in cases.items():
        assert nlu.parse(text)["intent"] == want, text

def test_template_holdout_accuracy():
    corpus = build_corpus()
    train, test = train_test_split(corpus)
    nlu = HinglishNLU().train(train)
    acc = sum(1 for t, y in test if nlu.parse(t)["intent"] == y) / len(test)
    assert acc >= 0.95, acc

def test_handwritten_eval_accuracy():
    train, _ = train_test_split(build_corpus())
    nlu = HinglishNLU().train(train)
    ev = json.loads(Path("data/eval_handwritten.json").read_text())
    acc = sum(1 for e in ev if nlu.parse(e["text"])["intent"] == e["intent"]) / len(ev)
    assert acc >= 0.90, acc

def test_amount_on_handwritten():
    train, _ = train_test_split(build_corpus())
    nlu = HinglishNLU().train(train)
    ev = [e for e in json.loads(Path("data/eval_handwritten.json").read_text()) if "amount" in e]
    acc = sum(1 for e in ev if nlu.parse(e["text"])["amount"] == e["amount"]) / len(ev)
    assert acc >= 0.95, acc

def test_name_extraction_person_intents_only():
    nlu = _trained()
    assert nlu.parse("ramesh ko 500 udhaar diya")["name"] == "Ramesh"
    assert nlu.parse("bijli ka bill 800")["name"] is None   # 'bijli' is not a customer

def test_model_roundtrip(tmp_path):
    nlu = _trained()
    p = tmp_path / "m.json"
    nlu.save(str(p))
    nlu2 = HinglishNLU.load(str(p))
    assert nlu2.parse("ramesh ko 500 udhaar diya")["intent"] == "udhaar_diya"

def test_nb_serializes_vocab():
    nb = NaiveBayes().fit([("a b", "x"), ("c d", "y")])
    d = nb.to_json()
    assert set(d["class_doc_counts"]) == {"x", "y"}
