"""
xbee_helper.device

Provides the main ZigBee class of the project and contains various constants
and utility functions to support it.
"""
import logging
from datetime import datetime, timedelta
from time import sleep
from sys import version_info

from xbee import ZigBee as ZigBeeDevice

from xbee_helper import exceptions


_LOGGER = logging.getLogger(__name__)
RX_TIMEOUT = timedelta(seconds=10)

# @TODO: Split these out to a separate module containing the
#        specifics for each type of XBee module. (This is Series 2 non-pro)
DIGITAL_PINS = (
    "dio-0", "dio-1", "dio-2",
    "dio-3", "dio-4", "dio-5",
    "dio-10", "dio-11", "dio-12"
)
ANALOG_PINS = (
    "adc-0", "adc-1", "adc-2", "adc-3"
)
IO_PIN_COMMANDS = (
    b"D0", b"D1", b"D2",
    b"D3", b"D4", b"D5",
    b"P0", b"P1", b"P2"
)
ADC_MAX_VAL = 1023


class GPIOSetting:
    """
    Class to contain a human readable name and byte value of a GPIO setting.
    """
    def __init__(self, name, value):
        self._name = name
        self._value = value

    def __str__(self):
        return self.name

    @property
    def name(self):
        """
        Human readable name for the GPIO setting.
        """
        return self._name

    @property
    def value(self):
        """
        Byte value of the GPIO setting.
        """
        return self._value


GPIO_DISABLED = GPIOSetting("DISABLED", b"\x00")
GPIO_STANDARD_FUNC = GPIOSetting("STANDARD_FUNC", b"\x01")
GPIO_ADC = GPIOSetting("ADC", b"\x02")
GPIO_DIGITAL_INPUT = GPIOSetting("DIGITAL_INPUT", b"\x03")
GPIO_DIGITAL_OUTPUT_LOW = GPIOSetting("DIGITAL_OUTPUT_LOW", b"\x04")
GPIO_DIGITAL_OUTPUT_HIGH = GPIOSetting("DIGITAL_OUTPUT_HIGH", b"\x05")
GPIO_SETTINGS = {
    GPIO_DISABLED.value: GPIO_DISABLED,
    GPIO_STANDARD_FUNC.value: GPIO_STANDARD_FUNC,
    GPIO_ADC.value: GPIO_ADC,
    GPIO_DIGITAL_INPUT.value: GPIO_DIGITAL_INPUT,
    GPIO_DIGITAL_OUTPUT_LOW.value: GPIO_DIGITAL_OUTPUT_LOW,
    GPIO_DIGITAL_OUTPUT_HIGH.value: GPIO_DIGITAL_OUTPUT_HIGH
}


def raise_if_error(frame):
    """
    Checks a frame and raises the relevant exception if required.
    """
    if "status" not in frame or frame["status"] == b"\x00":
        return
    codes_and_exceptions = {
        b"\x01": exceptions.ZigBeeUnknownError,
        b"\x02": exceptions.ZigBeeInvalidCommand,
        b"\x03": exceptions.ZigBeeInvalidParameter,
        b"\x04": exceptions.ZigBeeTxFailure
    }
    if frame["status"] in codes_and_exceptions:
        raise codes_and_exceptions[frame["status"]]()
    raise exceptions.ZigBeeUnknownStatus()


def hex_to_int(value):
    """
    Convert hex string like "AE3" to 2787.
    """
    if version_info.major >= 3:
        return int.from_bytes(value, "big")
    return int(value.encode("hex"), 16)


class ZigBee(object):
    """
    Adds convenience methods for a ZigBee.
    """
    _rx_frames = {}
    _frame_id = 1

    def __init__(self, ser):
        self._ser = ser
        # I think it's obvious that zb refers to a ZigBee.
        # pylint: disable=invalid-name
        self.zb = ZigBeeDevice(ser, callback=self._frame_received)

    @property
    def next_frame_id(self):
        """
        Gets a byte of the next valid frame ID (1 - 255), increments the
        internal _frame_id counter and wraps it back to 1 if necessary.
        """
        # Python 2/3 compatible way of converting 1 to "\x01" in py2 or b"\x01"
        # in py3.
        fid = bytes(bytearray((self._frame_id,)))
        self._frame_id += 1
        if self._frame_id > 0xFF:
            self._frame_id = 1
        try:
            del self._rx_frames[fid]
        except KeyError:
            pass
        return fid

    def _frame_received(self, frame):
        """
        Put the frame into the _rx_frames dict with a key of the frame_id.
        """
        try:
            self._rx_frames[frame["frame_id"]] = frame
        except KeyError:
            # Has no frame_id, ignore?
            pass
        _LOGGER.debug("Frame received: %s", frame)

    def _send(self, **kwargs):
        """
        Send a frame to either the local ZigBee or a remote device.
        """
        if kwargs.get("dest_addr_long") is not None:
            self.zb.remote_at(**kwargs)
        else:
            self.zb.at(**kwargs)

    def _send_and_wait(self, **kwargs):
        """
        Send a frame to either the local ZigBee or a remote device and wait
        for a pre-defined amount of time for its response.
        """
        frame_id = self.next_frame_id
        kwargs.update(dict(frame_id=frame_id))
        self._send(**kwargs)
        timeout = datetime.now() + RX_TIMEOUT
        while datetime.now() < timeout:
            try:
                frame = self._rx_frames.pop(frame_id)
                raise_if_error(frame)
                return frame
            except KeyError:
                sleep(0.1)
                continue
        _LOGGER.exception(
            "Did not receive response within configured timeout period.")
        raise exceptions.ZigBeeResponseTimeout()

    def _get_parameter(self, parameter, dest_addr_long=None):
        """
        Fetches and returns the value of the specified parameter.
        """
        frame = self._send_and_wait(
            command=parameter, dest_addr_long=dest_addr_long)
        return frame["parameter"]

    def get_sample(self, dest_addr_long=None):
        """
        Initiate a sample and return its data.
        """
        frame = self._send_and_wait(
            command=b"IS", dest_addr_long=dest_addr_long)
        if "parameter" in frame:
            # @TODO: Is there always one value? Is it always a list?
            return frame["parameter"][0]
        return {}

    def read_digital_pin(self, pin_number, dest_addr_long=None):
        """
        Fetches a sample and returns the boolean value of the requested digital
        pin.
        """
        sample = self.get_sample(dest_addr_long=dest_addr_long)
        try:
            return sample[DIGITAL_PINS[pin_number]]
        except KeyError:
            raise exceptions.ZigBeePinNotConfigured(
                "Pin %s (%s) is not configured as a digital input or output."
                % (pin_number, IO_PIN_COMMANDS[pin_number]))

    def read_analog_pin(self, pin_number, dest_addr_long=None):
        """
        Fetches a sample and returns the integer value of the requested analog
        pin.
        """
        sample = self.get_sample(dest_addr_long=dest_addr_long)
        try:
            return sample[ANALOG_PINS[pin_number]]
        except KeyError:
            raise exceptions.ZigBeePinNotConfigured(
                "Pin %s (%s) is not configured as an analog input." % (
                    pin_number, IO_PIN_COMMANDS[pin_number]))

    def set_gpio_pin(self, pin_number, setting, dest_addr_long=None):
        """
        Set a gpio pin setting.
        """
        assert setting in GPIO_SETTINGS.values()
        self._send_and_wait(
            command=IO_PIN_COMMANDS[pin_number],
            parameter=setting.value,
            dest_addr_long=dest_addr_long)

    def get_gpio_pin(self, pin_number, dest_addr_long=None):
        """
        Get a gpio pin setting.
        """
        frame = self._send_and_wait(
            command=IO_PIN_COMMANDS[pin_number], dest_addr_long=dest_addr_long)
        value = frame["parameter"]
        return GPIO_SETTINGS[value]

    def get_supply_voltage(self, dest_addr_long=None):
        """
        Fetches the value of %V and returns it as volts.
        """
        value = self._get_parameter(b"%V", dest_addr_long=dest_addr_long)
        return (hex_to_int(value) * (1200/1024.0)) / 1000

    def get_node_name(self, dest_addr_long=None):
        """
        Fetches and returns the value of NI.
        """
        return self._get_parameter(b"NI", dest_addr_long=dest_addr_long)

    def get_temperature(self, dest_addr_long=None):
        """
        Fetches and returns the degrees Celcius value measured by the XBee Pro
        module.
        """
        return hex_to_int(self._get_parameter(
            b"TP", dest_addr_long=dest_addr_long))
