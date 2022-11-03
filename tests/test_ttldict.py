from time import sleep

import pytest
from RestlessFunnelBot.ttldict import TTLDict

from utils import do_test, setup

setup()

TTL = 0.3
B_TTL = 0.5
S_TTL = 0.1
KEY = 3
VALUE = 14
OBJ = object()


def contains(data, KEY):
    return dict.__contains__(data, KEY)


def getitem(data, KEY):
    return dict.__getitem__(data, KEY).value


def test_geti_seti_smaller_time():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    data[KEY] = VALUE

    sleep(S_TTL)
    assert getitem(data, KEY) == VALUE
    assert data[KEY] == VALUE


def test_geti_seti_bigger_time():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    data[KEY] = VALUE

    sleep(B_TTL)
    assert contains(data, KEY)
    assert KEY in data


def test_geti_seti_smaller_time_expire():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    data[KEY] = VALUE

    sleep(S_TTL)
    assert getitem(data, KEY) == VALUE
    data.expire()
    assert getitem(data, KEY) == VALUE
    assert data[KEY] == VALUE


def test_geti_seti_bigger_time_expire():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    data[KEY] = VALUE

    sleep(B_TTL)
    assert getitem(data, KEY) == VALUE
    data.expire()
    assert not contains(data, KEY)
    assert KEY not in data


def test_get():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    assert data.get(KEY) is None
    assert data.get(KEY, OBJ) is OBJ

    data[KEY] = VALUE
    assert data.get(KEY) == VALUE
    assert data.get(KEY, OBJ) == VALUE


def test_get_smaller_time():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    data[KEY] = VALUE

    sleep(S_TTL)
    assert data.get(KEY) == VALUE
    assert data.get(KEY, OBJ) == VALUE


def test_get_bigger_time():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    data[KEY] = VALUE

    sleep(B_TTL)
    assert data.get(KEY) is None
    assert data.get(KEY, OBJ) is OBJ


def test_get_smaller_time_expire():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    data[KEY] = VALUE

    sleep(S_TTL)
    assert getitem(data, KEY) == VALUE
    data.expire()
    assert data.get(KEY) == VALUE
    assert data.get(KEY, OBJ) == VALUE


def test_get_bigger_time_expire():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    data[KEY] = VALUE

    sleep(B_TTL)
    assert getitem(data, KEY) == VALUE
    data.expire()
    assert data.get(KEY) is None
    assert data.get(KEY, OBJ) is OBJ


def test_pop():
    data: TTLDict[int, int] = TTLDict(TTL)

    assert not contains(data, KEY)
    with pytest.raises(KeyError):
        data.pop(KEY)
    assert not contains(data, KEY)
    assert data.pop(KEY, OBJ) is OBJ
    assert not contains(data, KEY)

    data[KEY] = VALUE
    assert data.pop(KEY) == VALUE
    assert not contains(data, KEY)
    data[KEY] = VALUE
    assert data.pop(KEY, OBJ) == VALUE
    assert not contains(data, KEY)


if __name__ == "__main__":
    do_test(__file__)
