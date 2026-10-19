from bolledger.transliterate import to_roman, has_devanagari


def test_basic_sentence():
    assert to_roman("रमेश को 500 उधार दिया") == "ramesh ko 500 udhaar diyaa"


def test_amount_words():
    assert to_roman("पांच सौ") == "paanch sau"
    assert to_roman("ढाई सौ") == "dhai sau"
    assert to_roman("डेढ़") == "dedh"


def test_devanagari_digits():
    assert to_roman("रमेश को ५०० दिया") == "ramesh ko 500 diyaa"


def test_mixed_and_detection():
    assert has_devanagari("रमेश 500")
    assert not has_devanagari("ramesh 500")
    assert to_roman("Ramesh ko 500 diya") == "ramesh ko 500 diya"
