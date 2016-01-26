import pytest

from xbee_helper import device, exceptions, ZigBee


def test_raise_if_error_no_status():
    """
    Should return None without raising if there's no "status" key in frame.
    """
    assert device.raise_if_error({}) is None


def test_raise_if_error_zero():
    """
    Should return None without raising if "status" is set to b"\x00".
    """
    assert device.raise_if_error(dict(status=b"\x00")) is None


def test_raise_if_error_unknown():
    """
    Should raise ZigBeeUnknownError if "status" is set to b"\x01".
    """
    with pytest.raises(exceptions.ZigBeeUnknownError):
        device.raise_if_error(dict(status=b"\x01"))


def test_raise_if_error_invalid_cmd():
    """
    Should raise ZigBeeInvalidCommand if "status" is set to b"\x02".
    """
    with pytest.raises(exceptions.ZigBeeInvalidCommand):
        device.raise_if_error(dict(status=b"\x02"))


def test_raise_if_error_invalid_param():
    """
    Should raise ZigBeeInvalidParameter if "status" is set to b"\x03".
    """
    with pytest.raises(exceptions.ZigBeeInvalidParameter):
        device.raise_if_error(dict(status=b"\x03"))


def test_raise_if_error_tx_failure():
    """
    Should raise ZigBeeTxFailure if "status" is set to b"\x04".
    """
    with pytest.raises(exceptions.ZigBeeTxFailure):
        device.raise_if_error(dict(status=b"\x04"))


def test_raise_if_error_unknown_status():
    """
    Should raise ZigBeeUnknownStatus if "status" is unrecognised.
    """
    with pytest.raises(exceptions.ZigBeeUnknownStatus):
        device.raise_if_error(dict(status=b"\xFF"))
