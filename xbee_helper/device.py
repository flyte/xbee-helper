"""
xbee_helper.device

Provides the main ZigBee class of the project and contains various constants
and utility functions to support it.
"""
import logging
from datetime import datetime
from time import sleep
from sys import version_info
from multiprocessing import Lock

from xbee import ZigBee as ZigBeeDevice

from xbee_helper import exceptions
from xbee_helper import const


_LOGGER = logging.getLogger(__name__)


# @TODO: Move me somewhere more appropriate.
MAX_VOLTAGE = 1.2


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


def adc_to_percentage(value, max_volts, clamp=True):
    """
    Convert the ADC raw value to a percentage.
    """
    percentage = (100.0 / const.ADC_MAX_VAL) * value
    return max(min(100, percentage), 0) if clamp else percentage


def adc_to_volts(value, max_volts):
    """
    Convert the ADC raw value to Volts.
    """
    return (float(max_volts) / const.ADC_MAX_VAL) * value


def adc_to_millivolts(value, max_volts):
    """
    Convert the ADC raw value to Millivolts
    """
    return int(adc_to_volts(value, max_volts) * 1000)


def convert_adc(value, output_type, max_volts):
    """
    Converts the output from the ADC into the desired type.
    """
    return {
        const.ADC_RAW: lambda x: x,
        const.ADC_PERCENTAGE: adc_to_percentage,
        const.ADC_VOLTS: adc_to_volts,
        const.ADC_MILLIVOLTS: adc_to_millivolts
    }[output_type](value, max_volts)


class ZigBee(object):
    """
    Adds convenience methods for a ZigBee.
    """
    _rx_frames = {}
    _frame_id = 1
    _lock = Lock()

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
        with self._lock:
            self._send(**kwargs)
            timeout = datetime.now() + const.RX_TIMEOUT
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
            return sample[const.DIGITAL_PINS[pin_number]]
        except KeyError:
            raise exceptions.ZigBeePinNotConfigured(
                "Pin %s (%s) is not configured as a digital input or output."
                % (pin_number, const.IO_PIN_COMMANDS[pin_number]))

    def read_analog_pin(
            self, pin_number, adc_max_volts,
            dest_addr_long=None, output_type=const.ADC_RAW):
        """
        Fetches a sample and returns the integer value of the requested analog
        pin. output_type should be one of the following constants from
        xbee_helper.const:
        - ADC_RAW
        - ADC_PERCENTAGE
        - ADC_VOLTS
        - ADC_MILLIVOLTS
        """
        sample = self.get_sample(dest_addr_long=dest_addr_long)
        try:
            return convert_adc(
                sample[const.ANALOG_PINS[pin_number]],
                output_type,
                adc_max_volts
            )
        except KeyError:
            raise exceptions.ZigBeePinNotConfigured(
                "Pin %s (%s) is not configured as an analog input." % (
                    pin_number, const.IO_PIN_COMMANDS[pin_number]))

    def set_gpio_pin(self, pin_number, setting, dest_addr_long=None):
        """
        Set a gpio pin setting.
        """
        assert setting in const.GPIO_SETTINGS.values()
        self._send_and_wait(
            command=const.IO_PIN_COMMANDS[pin_number],
            parameter=setting.value,
            dest_addr_long=dest_addr_long)

    def get_gpio_pin(self, pin_number, dest_addr_long=None):
        """
        Get a gpio pin setting.
        """
        frame = self._send_and_wait(
            command=const.IO_PIN_COMMANDS[pin_number],
            dest_addr_long=dest_addr_long
        )
        value = frame["parameter"]
        return const.GPIO_SETTINGS[value]

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
