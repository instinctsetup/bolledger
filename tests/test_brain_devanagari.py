import pytest
from bolledger.brain import handle_text
from bolledger.nlu import HinglishNLU
from bolledger.ledger import Ledger
import os

MODEL = os.path.join(os.path.dirname(__file__), "..", "bolledger", "nlu_model.json")


@pytest.fixture(scope="module")
def nlu():
    return HinglishNLU.load(MODEL)


@pytest.fixture
def ledger():
    return Ledger(":memory:")


def test_devanagari_udhaar(nlu, ledger):
    r = handle_text("रमेश को पांच सौ उधार दिया", nlu, ledger)
    assert r["parse"]["intent"] == "udhaar_diya"
    assert r["parse"]["amount"] == 500.0
    assert "500" in r["reply"]


def test_devanagari_jama(nlu, ledger):
    r = handle_text("सुरेश ने दो सौ जमा किया", nlu, ledger)
    assert r["parse"]["intent"] == "jama"
    assert r["parse"]["amount"] == 200.0


def test_devanagari_kharcha(nlu, ledger):
    r = handle_text("बिजली का बिल 800", nlu, ledger)
    assert r["parse"]["intent"] == "kharcha"
    assert r["parse"]["amount"] == 800.0


def test_devanagari_bikri(nlu, ledger):
    r = handle_text("आज 1500 की बिक्री हुई", nlu, ledger)
    assert r["parse"]["intent"] == "bikri"
    assert r["parse"]["amount"] == 1500.0


def test_devanagari_dhai(nlu, ledger):
    r = handle_text("मोहन को ढाई सौ उधार", nlu, ledger)
    assert r["parse"]["intent"] == "udhaar_diya"
    assert r["parse"]["amount"] == 250.0
