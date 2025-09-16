#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ILI9488 MicroPython driver
"""

import time, machine

# Commands
TFT_NOP = 0x00
TFT_SWRST = 0x01
TFT_SLPIN = 0x10
TFT_SLPOUT = 0x11
TFT_INVOFF = 0x20
TFT_INVON = 0x21
TFT_DISPOFF = 0x28
TFT_DISPON = 0x29
TFT_CASET = 0x2A
TFT_PASET = 0x2B
TFT_RAMWR = 0x2C
TFT_RAMRD = 0x2E
TFT_MADCTL = 0x36

def RGB(r, g, b):
    """Return RGB color value.

    Args:
        r (int): Red value.
        g (int): Green value.
        b (int): Blue value.
    """
    return r, g, b

class ILI9488:
    """ILI9488 driver class"""
    # Predefined RGB color constants
    BLACK   = RGB(0, 0, 0)
    WHITE   = RGB(255, 255, 255)
    RED     = RGB(255, 0, 0)
    GREEN   = RGB(0, 255, 0)
    BLUE    = RGB(0, 0, 255)
    YELLOW  = RGB(255, 255, 0)
    CYAN    = RGB(0, 255, 255)
    MAGENTA = RGB(255, 0, 255)
    GRAY    = RGB(128, 128, 128)
    ORANGE  = RGB(255, 165, 0)
    PURPLE  = RGB(128, 0, 128)

    def __init__(self, spi, cs, dc, rst, rotation=0, font = None):
        """Init display"""
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.width = 480
        self.height = 320
        self.rotation = rotation
        self.font = font

        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=1)
        self.rst.init(self.rst.OUT, value=1)

        self.reset()
        self.init_display()
        self.rotate(rotation)

    def rotate(self, rotation):
        """Set display rotation.
        
        Args:
            rotation (int): Screen orientation (0, 90, 180, 270 degrees)
        """
        rotation = rotation % 360  # Normalize to 0-359 degrees
        self.rotation = rotation
        madctl = 0x28  # MX=1, MV=0, MY=0
        
        # Map rotation to MADCTL values (BGR bit always set)
        if rotation == 0:
            madctl = 0x28
            self.width = 480
            self.height = 320
        elif rotation == 90:
            madctl = 0x48
            self.width = 320
            self.height = 480
        elif rotation == 180:
            madctl = 0xE8
            self.width = 480
            self.height = 320
        elif rotation == 270:
            madctl = 0x88
            self.width = 320
            self.height = 480
        else:
            print("Invalid rotation value, skipping...")

        # Send new configuration to display
        self.write_cmd(TFT_MADCTL)
        self.write_data(madctl)

    def reset(self):
        """Reset display"""
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(50)

    def write_cmd(self, cmd):
        """Write command"""
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        """Write data"""
        self.cs.value(0)
        self.dc.value(1)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)

    def init_display(self):
        """Initialize display"""
        self.write_cmd(0xE0) # Positive Gamma Control
        self.write_data(0x00)
        self.write_data(0x03)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x16)
        self.write_data(0x0A)
        self.write_data(0x3F)
        self.write_data(0x78)
        self.write_data(0x4C)
        self.write_data(0x09)
        self.write_data(0x0A)
        self.write_data(0x08)
        self.write_data(0x16)
        self.write_data(0x1A)
        self.write_data(0x0F)

        self.write_cmd(0XE1) # Negative Gamma Control
        self.write_data(0x00)
        self.write_data(0x16)
        self.write_data(0x19)
        self.write_data(0x03)
        self.write_data(0x0F)
        self.write_data(0x05)
        self.write_data(0x32)
        self.write_data(0x45)
        self.write_data(0x46)
        self.write_data(0x04)
        self.write_data(0x0E)
        self.write_data(0x0D)
        self.write_data(0x35)
        self.write_data(0x37)
        self.write_data(0x0F)

        self.write_cmd(0XC0) # Power Control 1
        self.write_data(0x17)
        self.write_data(0x15)

        self.write_cmd(0xC1) # Power Control 2
        self.write_data(0x41)

        self.write_cmd(0xC5) # VCOM Control
        self.write_data(0x00)
        self.write_data(0x12)
        self.write_data(0x80)

        self.write_cmd(0x3A) # Pixel Interface Format
        self.write_data(0x66) # 18-bit colour for SPI

        self.write_cmd(0xB0) # Interface Mode Control
        self.write_data(0x00)

        self.write_cmd(0xB1) # Frame Rate Control
        self.write_data(0xA0)

        self.write_cmd(0xB4) # Display Inversion Control
        self.write_data(0x02)

        self.write_cmd(0xB6) # Display Function Control
        self.write_data(0x02)
        self.write_data(0x02)
        self.write_data(0x3B)

        self.write_cmd(0xB7) # Entry Mode Set
        self.write_data(0xC6)

        self.write_cmd(0xF7) # Adjust Control 3
        self.write_data(0xA9)
        self.write_data(0x51)
        self.write_data(0x2C)
        self.write_data(0x82)

        self.write_cmd(TFT_SLPOUT) #Exit Sleep
        time.sleep_ms(120)

        self.write_cmd(TFT_DISPON) #Display on
        time.sleep_ms(25)

    def fill_screen(self, color):
        """Fill screen with color"""
        self.set_window(0, 0, self.width - 1, self.height - 1)
        r, g, b = color
        buf = bytearray(3 * self.width)
        for i in range(self.width):
            buf[3 * i] = r
            buf[3 * i + 1] = g
            buf[3 * i + 2] = b
        for i in range(self.height):
            self.write_data(buf)

    def fill_rect(self, x, y, width, height, color):
        """Draw a filled rectangle.
        
        Args:
            x, y (int): Top-left corner coordinates
            width, height (int): Dimensions of rectangle
            color (tuple): RGB color (r, g, b)
        """
        # Validate coordinates
        if x >= self.width or y >= self.height:
            return
            
        # Clamp to display boundaries
        x_end = min(x + width - 1, self.width - 1)
        y_end = min(y + height - 1, self.height - 1)
        
        # Calculate actual dimensions after clamping
        actual_width = x_end - x + 1
        actual_height = y_end - y + 1
        
        # Set drawing window
        self.set_window(x, y, x_end, y_end)
        
        # Prepare color data
        r, g, b = color
        buf = bytearray(3 * actual_width)
        
        # Fill buffer with color
        for i in range(actual_width):
            buf[3 * i] = r
            buf[3 * i + 1] = g
            buf[3 * i + 2] = b
        
        # Write rows
        for _ in range(actual_height):
            self.write_data(buf)

    def set_window(self, x0, y0, x1, y1):
        """Set window for drawing"""
        self.write_cmd(TFT_CASET) # Column address set
        self.write_data(x0 >> 8)
        self.write_data(x0 & 0xFF)
        self.write_data(x1 >> 8)
        self.write_data(x1 & 0xFF)

        self.write_cmd(TFT_PASET) # Page address set
        self.write_data(y0 >> 8)
        self.write_data(y0 & 0xFF)
        self.write_data(y1 >> 8)
        self.write_data(y1 & 0xFF)

        self.write_cmd(TFT_RAMWR) # Memory write

    def pixel(self, x, y, color):
        """Draw a pixel"""
        self.set_window(x, y, x, y)
        r, g, b = color
        self.write_data(r)
        self.write_data(g)
        self.write_data(b)

    def hline(self, x, y, w, color):
        """Draw a horizontal line"""
        self.set_window(x, y, x + w - 1, y)
        r, g, b = color
        buf = bytearray(3 * w)
        for i in range(w):
            buf[3 * i] = r
            buf[3 * i + 1] = g
            buf[3 * i + 2] = b
        self.write_data(buf)

    def vline(self, x, y, h, color):
        """Draw a vertical line"""
        self.set_window(x, y, x, y + h - 1)
        r, g, b = color
        buf = bytearray(3 * h)
        for i in range(h):
            buf[3 * i] = r
            buf[3 * i + 1] = g
            buf[3 * i + 2] = b
        self.write_data(buf)

    def rect(self, x, y, w, h, color):
        """Draw a rectangle"""
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def line(self, x0, y0, x1, y1, color):
        """Draw a line using Bresenham's algorithm"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
    
    def text(self, x, y, text_str, color,  scale=1, background_color=None, spacing=1):
        """Draw text using the loaded font with optional scaling
        
        Args:
            x, y (int): Starting coordinates
            text_str (str): Text to display
            color (tuple): RGB color (r, g, b)
            scale (int, optional): Scaling factor (>=1). Defaults to 1.
            background_color (tuple, optional): Background RGB color. Defaults to None.
        """
        if not self.font:
            print("Error: Font not loaded. Call set_font() first or pass font to constructor.")
            return
        if scale < 1:
            scale = 1  # Ensure scale is at least 1

        current_x = x
        for char_code in text_str:
            char_data, char_width, char_height = self.font.get_letter(char_code, color, background_color)
            if char_data:
                scaled_width = char_width * scale
                scaled_height = char_height * scale
                
                if scale == 1:
                    # No scaling needed - use original data
                    self.set_window(current_x, y, current_x + char_width - 1, y + char_height - 1)
                    self.write_data(char_data)
                else:
                    # Create scaled character buffer
                    scaled_data = bytearray(3 * scaled_width * scaled_height)
                    src_idx = 0
                    dest_idx = 0
                    
                    # Scale vertically (repeat each row 'scale' times)
                    for _ in range(char_height):
                        row_buffer = bytearray(3 * scaled_width)
                        row_idx = 0
                        
                        # Scale horizontally (repeat each pixel 'scale' times)
                        for _ in range(char_width):
                            pixel = char_data[src_idx:src_idx+3]
                            src_idx += 3
                            for _ in range(scale):
                                row_buffer[row_idx:row_idx+3] = pixel
                                row_idx += 3
                        
                        # Repeat scaled row 'scale' times
                        for _ in range(scale):
                            scaled_data[dest_idx:dest_idx+len(row_buffer)] = row_buffer
                            dest_idx += len(row_buffer)
                    
                    # Draw scaled character
                    self.set_window(current_x, y, current_x + scaled_width - 1, y + scaled_height - 1)
                    self.write_data(scaled_data)
                
                # Move cursor (add spacing pixels space between characters)
                current_x += scaled_width + spacing

    def set_font(self, font_obj):
        """Set the font for the display"""
        self.font = font_obj
    
    def image(self, x, y, w, h, data):
        """Display an RGB666 image at specified coordinates.
        
        Args:
            x, y (int): Top-left corner coordinates
            w, h (int): width and length of image
            data (bytes): RGB666 image data (3 bytes per pixel)
        """
        self.set_window(x, y, x + w - 1, y + h - 1)
        self.write_data(data)