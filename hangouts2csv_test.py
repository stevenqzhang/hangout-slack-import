__author__ = 'steven'
from hangouts2csv import is_name, UserNames

def test_isname():
    assert is_name("Steven Zhang") == True
    assert is_name("+ 123190 123098 12") == False
    assert is_name("+1 (123) 121880 ") == False


def test_generateCanonicalName_yesName():
    n1 = UserNames({"123123", "First Name", "231231 not a name"})
    n1.generateCanonicalName()
    assert n1.canonical_name == "First Name"


def test_generateCanonicalName_noName():
    n1 = UserNames({"123123", "123123123", "231231 not a name"})
    n1.generateCanonicalName()
    assert n1.canonical_name == "unknown"