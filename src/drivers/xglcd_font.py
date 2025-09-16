"""XGLCD Font Utility."""
from math import ceil, floor


class XglcdFont(object):
    """Font data in X-GLCD format.

    Attributes:
        letters: A bytearray of letters (columns consist of bytes)
        width: Maximum pixel width of font
        height: Pixel height of font
        start_letter: ASCII number of first letter
        height_bytes: How many bytes comprises letter height

    Note:
        Font files can be generated with the free version of MikroElektronika
        GLCD Font Creator:  www.mikroe.com/glcd-font-creator
        The font file must be in X-GLCD 'C' format.
        To save text files from this font creator program in Win7 or higher
        you must use XP compatibility mode or you can just use the clipboard.
    """

    # Dict to translate bitwise values to byte position
    BIT_POS = {1: 0, 2: 2, 4: 4, 8: 6, 16: 8, 32: 10, 64: 12, 128: 14, 256: 16}

    def __init__(self, path, width, height, start_letter=32, letter_count=96):
        """Constructor for X-GLCD Font object.

        Args:
            path (string): Full path of font file
            width (int): Maximum width in pixels of each letter
            height (int): Height in pixels of each letter
            start_letter (int): First ASCII letter.  Default is 32.
            letter_count (int): Total number of letters.  Default is 96.
        """
        self.width = width
        self.height = max(height, 8)
        self.start_letter = start_letter
        self.letter_count = letter_count
        self.bytes_per_letter = (floor(
            (self.height - 1) / 8) + 1) * self.width + 1
        self.__load_xglcd_font(path)

    def __load_xglcd_font(self, path):
        """Load X-GLCD font data from text file.

        Args:
            path (string): Full path of font file.
        """
        bytes_per_letter = self.bytes_per_letter
        # Buffer to hold letter byte values
        self.letters = bytearray(bytes_per_letter * self.letter_count)
        mv = memoryview(self.letters)
        offset = 0
        with open(path, 'r') as f:
            for line in f:
                # Skip lines that do not start with hex values
                line = line.strip()
                if len(line) == 0 or line[0:2] != '0x':
                    continue
                # Remove comments
                comment = line.find('//')
                if comment != -1:
                    line = line[0:comment].strip()
                # Remove trailing commas
                if line.endswith(','):
                    line = line[0:len(line) - 1]
                # Convert hex strings to bytearray and insert in to letters
                mv[offset: offset + bytes_per_letter] = bytearray(
                    int(b, 16) for b in line.split(','))
                offset += bytes_per_letter
    
    def lit_bits(self, n):
        """Return positions of 1 bits only."""
        while n:
            b = n & (~n+1)
            yield self.BIT_POS[b]
            n ^= b

    def get_letter(self, letter, color, background=0):
        """Convert letter byte data to pixels.

        Args:
            letter (string): Letter to return (must exist within font).
            color (int): RGB color value.
            background (int): RGB background color (default: black).
        Returns:
            (bytearray): Pixel data in RGB666 format (3 bytes per pixel).
            (int, int): Letter width and height.
        """

        # Convert foreground color
        fg_r8, fg_g8, fg_b8 = color
        
        # Convert background color if provided
        if background:
            bg_r8, bg_g8, bg_b8 = background

        # Get index of letter
        letter_ord = ord(letter) - self.start_letter

        # Confirm font contains letter
        if letter_ord >= self.letter_count:
            print('Font does not contain character: ' + letter)
            return b'', 0, 0
        bytes_per_letter = self.bytes_per_letter
        offset = letter_ord * bytes_per_letter
        mv = memoryview(self.letters[offset:offset + bytes_per_letter])

        # Get width of letter (specified by first byte)
        letter_width = mv[0]
        letter_height = self.height
        # Calculate total pixels in the letter
        total_pixels = letter_width * letter_height
        
        # Create buffer (3 bytes per pixel for RGB666)
        if background:
            buf = bytearray([bg_r8, bg_g8, bg_b8] * total_pixels)
        else:
            buf = bytearray(total_pixels * 3)  # Default to black background

        # Calculate bytes per column (segments of 8 rows)
        bytes_per_col = ceil(letter_height / 8)
        col = 0
        segment = 0

        # Process each data byte after the width byte
        for i in range(1, len(mv)):
            byte = mv[i]
            row_in_segment = 0
            
            # Process each bit in the byte
            while byte:
                if byte & 1:
                    # Calculate position in buffer (row-major order)
                    row = segment * 8 + row_in_segment
                    if row < letter_height:
                        # Position: (row * letter_width + col) * 3
                        pos = (row * letter_width + col) * 3
                        buf[pos] = fg_r8
                        buf[pos + 1] = fg_g8
                        buf[pos + 2] = fg_b8
                byte >>= 1
                row_in_segment += 1
            
            # Move to next segment or next column
            segment += 1
            if segment >= bytes_per_col:
                segment = 0
                col += 1

        return buf, letter_width, letter_height

    def measure_text(self, text, scale=1, spacing=1):
        """Measure length of text string in pixels.

        Args:
            text (string): Text string to measure
            scale (optional int): Scaling factor of the text.  Default: 1.
            spacing (optional int): Pixel spacing between letters.  Default: 1.
        Returns:
            int: length of text
        """
        length = 0
        for letter in text:
            # Get index of letter
            letter_ord = ord(letter) - self.start_letter
            offset = letter_ord * self.bytes_per_letter
            # Add length of letter and spacing
            length += self.letters[offset] * scale + spacing
        return length
