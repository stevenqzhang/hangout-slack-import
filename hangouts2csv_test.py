__author__ = 'steven'
from hangouts2csv import is_name, UserNamesAndNumbers

def test_isname():
    assert is_name("Steven Zhang") == True
    assert is_name("+ 123190 123098 12") == False
    assert is_name("+1 (123) 121880 ") == False


def test_generateCanonicalName_yesName():
    n1 = UserNamesAndNumbers({"123123", "First Name", "231231 not a name"})
    n1.generateCanonicalName()
    assert n1.canonical_name == "First Name"


def test_generateCanonicalName_noName():
    n1 = UserNamesAndNumbers({"123123", "123123123", "231231 not a name"})
    n1.generateCanonicalName()
    assert n1.canonical_name == "unknown"

def test_formatNumber():
    assert UserNamesAndNumbers.formatNumber("123 456 7890") ==("+1234567890")
    assert UserNamesAndNumbers.formatNumber("123 123 1234") ==("+1231231234")

def test_generateNumbers_yesNumber():
    n1 = UserNamesAndNumbers({"1231231234", "1231231235", "231231 not a number"})
    n1.generateNumbers()
    assert n1.canonical_number == u"+1231231234"

if __name__ == '__main__':
    test_generateNumbers_yesNumber()