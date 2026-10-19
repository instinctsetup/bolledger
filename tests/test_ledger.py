import pytest
from bolledger.ledger import Ledger

@pytest.fixture
def led(tmp_path):
    l = Ledger(tmp_path / "t.db")
    yield l
    l.close()

def test_udhaar_and_balance(led):
    led.add("udhaar_diya", 500, "Ramesh")
    led.add("udhaar_diya", 300, "Ramesh")
    assert led.balance("Ramesh") == 800
    led.add("jama", 200, "Ramesh")
    assert led.balance("Ramesh") == 600

def test_customers_sorted_by_balance(led):
    led.add("udhaar_diya", 100, "A")
    led.add("udhaar_diya", 900, "B")
    names = [c["name"] for c in led.list_customers()]
    assert names[0] == "B"

def test_paise_no_float_drift(led):
    led.add("udhaar_diya", 0.1 + 0.2, "A")   # 0.30000000000000004 in float
    assert led.balance("A") == pytest.approx(0.30)

def test_hisaab(led):
    led.add("bikri", 1000)
    led.add("kharcha", 200)
    led.add("udhaar_diya", 500, "A")
    led.add("jama", 300, "A")
    h = led.hisaab()
    assert h["bikri"] == 1000 and h["kharcha"] == 200
    assert h["net_cash"] == 1000 + 300 - 200
    assert h["total_outstanding"] == 200

def test_delete(led):
    tx = led.add("bikri", 100)
    assert led.delete(tx["id"])
    assert led.hisaab()["bikri"] == 0

def test_bad_inputs(led):
    with pytest.raises(ValueError):
        led.add("udhaar_diya", -5, "A")
    with pytest.raises(ValueError):
        led.add("nonsense", 5)
