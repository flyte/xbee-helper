"""
xbee_helper.const

Constants used by the rest of the modules.
"""
from datetime import timedelta


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
ADC_RAW = 0
ADC_PERCENTAGE = 1
ADC_VOLTS = 2
ADC_MILLIVOLTS = 3


class GPIOSetting(object):
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
GPIO_SETTINGS = {x.value: x for x in (
    GPIO_DISABLED,
    GPIO_STANDARD_FUNC,
    GPIO_ADC,
    GPIO_DIGITAL_INPUT,
    GPIO_DIGITAL_OUTPUT_LOW,
    GPIO_DIGITAL_OUTPUT_HIGH
)}
