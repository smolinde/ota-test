# xpt2046.py
#
# MicroPython driver for the XPT2046 touchscreen controller, updated with
# IRQ support and screen rotation.

from time import sleep
from micropython import const

class Touch(object):
    """
    Serial interface for the XPT2046 Touch Screen Controller.
    """

    # Command opcodes for reading X and Y coordinates.
    # Note: GET_X and GET_Y might need to be swapped depending on wiring.
    GET_X = const(0x90)
    GET_Y = const(0xD0)

    def __init__(self, spi, cs, irq=None, rotation=0,
                 width=480, height=320,
                 x_min=120, x_max=1968, y_min=120, y_max=1800):
        """
        Initialize the touch screen controller.

        Args:
            spi (Class Spi): Configured SPI bus.
            cs (Class Pin): Chip select pin.
            irq (Class Pin, optional): Interrupt pin to detect touches.
            rotation (int): Screen rotation (0-3).
            width (int): Width of the LCD screen.
            height (int): Height of the LCD screen.
            x_min (int): Minimum raw X coordinate for calibration.
            x_max (int): Maximum raw X coordinate for calibration.
            y_min (int): Minimum raw Y coordinate for calibration.
            y_max (int): Maximum raw Y coordinate for calibration.
        """
        self.spi = spi
        self.cs = cs
        self.irq = irq
        self.cs.init(self.cs.OUT, value=1)
        if self.irq:
            self.irq.init(self.irq.IN)

        # Buffers for SPI communication
        self.rx_buf = bytearray(3)
        self.tx_buf = bytearray(3)

        self.width = width
        self.height = height
        self.rotation = rotation

        # Set calibration values
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

        # Pre-calculate multipliers for coordinate normalization
        self.x_multiplier = width / (x_max - x_min)
        self.x_add = -self.x_min * self.x_multiplier
        self.y_multiplier = height / (y_max - y_min)
        self.y_add = -self.y_min * self.y_multiplier

    def is_touched(self):
        """
        Return True if the screen is currently being touched, based on the IRQ pin.
        """
        if self.irq:
            return self.irq.value() == 0
        # Fallback if no IRQ pin is provided: check for a valid raw touch.
        return self.raw_touch() is not None

    def get_touch(self):
        """
        Take multiple samples to get an accurate, debounced touch reading.
        """
        if not self.is_touched():
            return None

        timeout = 2.0
        confidence = 5
        buffer = [[0, 0] for _ in range(confidence)]
        buf_len = confidence
        buf_ptr = 0
        nsamples = 0

        while timeout > 0:
            if nsamples == buf_len:
                mean_x = sum(c[0] for c in buffer) // buf_len
                mean_y = sum(c[1] for c in buffer) // buf_len
                dev = sum(
                    (c[0] - mean_x)**2 + (c[1] - mean_y)**2 for c in buffer
                ) / buf_len
                if dev <= 50:
                    return self.normalize(mean_x, mean_y)

            sample = self.raw_touch()
            if sample is None:
                nsamples = 0
            else:
                buffer[buf_ptr] = sample
                buf_ptr = (buf_ptr + 1) % buf_len
                nsamples = min(nsamples + 1, buf_len)

            sleep(0.05)
            timeout -= 0.05

        return None

    def normalize(self, x, y):
        """
        Convert raw coordinates to screen coordinates and apply rotation.
        """
        x = int(self.x_multiplier * x + self.x_add)
        y = int(self.y_multiplier * y + self.y_add)

        if self.rotation == 0:
            return x, y
        elif self.rotation == 1:
            return y, self.width - x
        elif self.rotation == 2:
            return self.width - x, self.height - y
        elif self.rotation == 3:
            return self.height - y, x
        return x, y # Default to no rotation if value is invalid

    def raw_touch(self):
        """
        Read raw X and Y touch values from the controller.
        """
        x = self.send_command(self.GET_X)
        y = self.send_command(self.GET_Y)

        if self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max:
            return (x, y)
        return None

    def send_command(self, command):
        """
        Send a command to the XPT2046 and read the 12-bit ADC value.
        """
        self.tx_buf[0] = command
        self.cs(0)
        self.spi.write_readinto(self.tx_buf, self.rx_buf)
        self.cs(1)
        return (self.rx_buf[1] << 4) | (self.rx_buf[2] >> 4)

