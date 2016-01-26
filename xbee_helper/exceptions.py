"""
xbee_helper.exceptions

Contains the various exceptions which could be raised when communicating with
the ZigBee network.
"""


class ZigBeeException(Exception):
    """
    One exception to rule them all. Catch this if you don't care why it failed.
    """
    pass


class ZigBeeResponseTimeout(ZigBeeException):
    """
    The ZigBee device didn't return a frame within the configured timeout.
    """
    pass


class ZigBeeUnknownError(ZigBeeException):
    """
    The ZigBee device returned an 0x01 status byte.
    """
    pass


class ZigBeeInvalidCommand(ZigBeeException):
    """
    The requested ZigBee command was not valid.
    """
    pass


class ZigBeeInvalidParameter(ZigBeeException):
    """
    The requested ZigBee parameter was not valid.
    """
    pass


class ZigBeeTxFailure(ZigBeeException):
    """
    The ZigBee device attempted to send the frame but it could not communicate
    with the target device (usually out of range or switched off).
    """
    pass


class ZigBeeUnknownStatus(ZigBeeException):
    """
    The ZigBee device returned a status code which we're not familiar with.
    """
    pass


class ZigBeePinNotConfigured(ZigBeeException):
    """
    An operation was attempted on a GPIO pin which it was not configured for.
    """
    pass
