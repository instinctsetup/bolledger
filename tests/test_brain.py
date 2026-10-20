from bolledger.brain import handle_text
from bolledger.corpus import build_corpus, train_test_split
from bolledger.nlu import HinglishNLU
from bolledger.ledger import Ledger

def _setup(tmp_path):
    train, _ = train_test_split(build_corpus())
    return HinglishNLU().train(train), Ledger(tmp_path / "b.db")

def test_full_flow(tmp_path):
    nlu, led = _setup(tmp_path)
    r = handle_text("Ramesh ko 500 udhaar diya", nlu, led)
    assert "500" in r["reply"] and r["action"]["kind"] == "udhaar_diya"
    r = handle_text("Ramesh ka kitna baaki hai", nlu, led)
    assert "500" in r["reply"]
    r = handle_text("Ramesh ne 200 jama kiya", nlu, led)
    assert "300" in r["reply"]

def test_missing_amount_asks(tmp_path):
    nlu, led = _setup(tmp_path)
    r = handle_text("Ramesh ko udhaar diya", nlu, led)
    assert "Amount" in r["reply"] or "Kitne" in r["reply"]

def test_missing_name_asks(tmp_path):
    nlu, led = _setup(tmp_path)
    r = handle_text("500 udhaar diya", nlu, led)
    assert "naam" in r["reply"].lower()

def test_unknown_graceful(tmp_path):
    nlu, led = _setup(tmp_path)
    r = handle_text("gaana bajao", nlu, led)
    assert "Samajh nahi aaya" in r["reply"]


def test_zero_amount_asks_again(tmp_path):
    nlu, led = _setup(tmp_path)
    r = handle_text("ramesh ko 0 udhaar diya", nlu, led)
    assert "action" not in r
    assert "Kitne" in r["reply"]
