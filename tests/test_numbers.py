from bolledger.numbers import parse_amount

def test_digits():
    assert parse_amount("ramesh ko 500 diya")[0] == 500

def test_words_simple():
    assert parse_amount("do sau")[0] == 200
    assert parse_amount("paanch sau")[0] == 500
    assert parse_amount("ek hazaar")[0] == 1000

def test_special():
    assert parse_amount("dedh sau")[0] == 150
    assert parse_amount("dhai hazaar")[0] == 2500
    assert parse_amount("sava lakh")[0] == 125000

def test_compound():
    assert parse_amount("do hazaar paanch sau")[0] == 2500
    assert parse_amount("teen sau pachaas")[0] == 350

def test_none():
    assert parse_amount("kaise ho")[0] is None
