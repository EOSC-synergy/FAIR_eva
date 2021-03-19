import pytest

@pytest.fixture
def test_all_indicators():
    response = {'findable': True, 'accessible': True,
        'interoperable': True, 'reusable': True}
    result = False
    for e in response:
        if (response[e]):
            result = response[e]
        else:
            result = response[e]
            break
    return result


def test_extra():
    result = 98
    assert result > 0
