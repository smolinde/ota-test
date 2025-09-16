from machine import Pin, SPI
from drivers.ILI9488 import ILI9488, RGB
import time

class DisplayManager:
    __ERROR_SCREEN_TIMEOUT = 20

    __STATION_DEFAULT_TEXT_LABELS = [
        "First Gas Station",
        "Second Gas Station",
        "Third Gas Station"
    ]
    __STATION_DEFAULT_FUEL_LABELS = {
        "e5": "Gas Price (E5)",
        "e10": "Gas Price (E10)",
        "diesel": "Diesel Price" 
    }
    __STATION_STATUS_COLOR = {
        "OPEN": RGB(0, 205, 0),
        "CLOSED": RGB(230, 0, 0),
        "NO PRICES": RGB(255, 150, 0),
        "STATUS UNKNOWN": RGB(255, 150, 0)
    }

    def __init__(self, ili_font, price_font=None):
        spi = SPI(2, baudrate=60000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=None)
        self.display = ILI9488(spi, Pin(14), Pin(12), Pin(13), 0, ili_font)
        self.currently_displayed = {
            "timedate" : [None] * 3,
            "weather_data" : [None] * 4,
            "weather_icon_name" : None,
            "station_statuses" : [None] * 3,
            "fuel_prices" : [None] * 3
        }
        self.ili_font = ili_font
        self.price_font = price_font
        self.clear_display()    

    def __ljust(self, s, width, fillchar = ' '):
        return s + (fillchar * (width - len(s)))
    
    def clear_display(self):
        self.display.fill_screen(ILI9488.WHITE)
    
    def draw_waiting_screen(self):
        self.clear_display()
        self.display.text(100, 141, "Please wait...", ILI9488.BLACK, 2, ILI9488.WHITE)

    def draw_waiting_for_wlan(self, wlan_icon, wlan_ssid):
        self.clear_display()
        wlan_ssid = wlan_ssid if len(wlan_ssid) < 21 else wlan_ssid[:18] + "..."
        self.display.image(10, 110, 100, 100, wlan_icon)
        self.display.text(125, 120, "Waiting for WLAN", ILI9488.BLACK, 2, ILI9488.WHITE)
        self.display.text(125, 160, "Trying to connect to:", ILI9488.BLACK, 1, ILI9488.WHITE)
        self.display.text(125, 180, wlan_ssid, ILI9488.BLACK, 1, ILI9488.WHITE)

    def draw_wlan_waiting_time(self, time_left):
        time_left = f"{time_left}" if len(f"{time_left}") > 1 else f" {time_left}"
        self.display.text(426, 180, f"{time_left}s", ILI9488.BLACK, 1, ILI9488.WHITE)
    
    def draw_error(self, error_number, error_text, error_qr_code):
        self.clear_display()
        self.display.text(10, 10, f"ERROR {error_number}", ILI9488.RED, 2, ILI9488.WHITE)
        self.display.image(370, 10, 100, 100, error_qr_code)
        self.display.text(10, 50, "(Scan QR code for help)", ILI9488.BLACK, 1, ILI9488.WHITE)
        for i in range(len(error_text)):
            self.display.text(10, 120 + 20 * i, error_text[i], ILI9488.BLACK, 1, ILI9488.WHITE)
        if error_number[0] == "1":
            self.display.text(81, 260, "[ Touch anywhere to restart ]", ILI9488.BLACK, 1, ILI9488.WHITE)
        else:
            self.display.text(114, 260, "[ Auto-restart in     ]", ILI9488.BLACK, 1, ILI9488.WHITE)
            for i in range(self.__ERROR_SCREEN_TIMEOUT + 1):
                self.__draw_error_waiting_time(self.__ERROR_SCREEN_TIMEOUT - i)
                time.sleep(1)
    
    def __draw_error_waiting_time(self, time_left):
        time_left = f"{time_left}" if len(f"{time_left}") > 1 else f" {time_left}"
        self.display.text(312, 260, f"{time_left}s", ILI9488.BLACK, 1, ILI9488.WHITE)

    def draw_main_layout(self, station_icons, weather_symbols, station_labels, fuel_type):
        self.clear_display()
        self.display.fill_rect(398, 0, 2, 80, ILI9488.BLACK)
        for i in range(2):
            self.display.fill_rect(0, 80 + 80 * i, 480, 2, ILI9488.BLACK)
        self.display.fill_rect(0, 39, 400, 2, ILI9488.BLACK)
        self.display.fill_rect(143, 0, 2, 40, ILI9488.BLACK)
        self.display.fill_rect(298, 0, 2, 40, ILI9488.BLACK)
        self.display.fill_rect(0, 160, 480, 2, ILI9488.BLACK)
        self.display.fill_rect(0, 240, 480, 2, ILI9488.BLACK)
        self.display.fill_rect(330, 80, 2, 240, ILI9488.BLACK)
        
        self.display.image(3, 44, 34, 34, weather_symbols[0])
        self.display.image(101, 43, 34, 34, weather_symbols[1])
        self.display.image(199, 44, 34, 34, weather_symbols[2])
        self.display.image(297, 43, 34, 34, weather_symbols[3])

        for i in range(3):
            self.display.image(8, 88 + 80 * i, 64, 64, station_icons[i])
            self.display.fill_rect(332, 82 + 80 * i, 148, 78, RGB(140, 240, 140))
            if station_labels[i][1] == "":
                self.display.text(90, 89 + 80 * i, self.__STATION_DEFAULT_TEXT_LABELS(i), ILI9488.BLACK, 1, ILI9488.WHITE)
            else:
                self.display.text(90, 89 + 80 * i,  station_labels[i][1][:21], ILI9488.BLACK, 1, ILI9488.WHITE)
            if station_labels[i][2] == "":
                self.display.text(90, 89 + 80 * i + 22, self.__STATION_DEFAULT_FUEL_LABELS.get(fuel_type), ILI9488.BLACK, 1, ILI9488.WHITE)
            else:
                self.display.text(90, 89 + 80 * i + 22,  station_labels[i][2][:21], ILI9488.BLACK, 1, ILI9488.WHITE)
    
    def draw_weekday_date_time(self, timedate):
        if timedate[0] != self.currently_displayed.get("timedate")[0]:
            self.currently_displayed["timedate"][0] = timedate[0]
            text_length = self.ili_font.measure_text(timedate[0])
            self.display.fill_rect(0, 0, 142, 39, ILI9488.WHITE)
            if timedate[0] == "SUNDAY":
                self.display.text(23 + (98 - text_length) // 2, 11, timedate[0], ILI9488.RED, 1, ILI9488.WHITE)
            else:
                self.display.text(23 + (98 - text_length) // 2, 11, timedate[0], ILI9488.BLACK, 1, ILI9488.WHITE)
        if timedate[1] != self.currently_displayed.get("timedate")[1]:
            self.currently_displayed["timedate"][1] = timedate[1]
            self.display.text(167, 11, timedate[1], ILI9488.BLACK, 1, ILI9488.WHITE)
        if timedate[2] != self.currently_displayed.get("timedate")[2]:
            self.currently_displayed["timedate"][2] = timedate[2]
            self.display.text(322, 11, timedate[2], ILI9488.BLACK, 1, ILI9488.WHITE)
    
    def draw_weather_data(self, weather_data, weather_icon_name, weather_icon=None):
        for i in range(len(weather_data)):
            if weather_data[i] != self.currently_displayed.get("weather_data")[i]:
                self.currently_displayed["weather_data"][i] = weather_data[i]
                self.display.text(42 + 98 * i, 51,  self.__ljust(weather_data[i], 5), ILI9488.BLACK, 1, ILI9488.WHITE)
        
        if weather_icon_name != self.currently_displayed.get("weather_icon_name"):
            self.currently_displayed["weather_icon_name"] = weather_icon_name
            self.display.image(400, 0, 80, 80, weather_icon)
    
    def draw_station_data(self, station_statuses, fuel_prices):
        for i in range(len(station_statuses)):
            if station_statuses[i] != self.currently_displayed.get("station_statuses")[i]:
                self.currently_displayed["station_statuses"][i] = station_statuses[i]
                status = station_statuses[i]
                self.display.text(90, 133 + 80 * i, self.__ljust(status, 14), self.__STATION_STATUS_COLOR.get(status), 1, ILI9488.WHITE)
        
        self.display.set_font(self.price_font)
        for i in range(len(fuel_prices)):
            if fuel_prices[i] != self.currently_displayed.get("fuel_prices")[i]:
                self.currently_displayed["fuel_prices"][i] = fuel_prices[i]
                self.display.text(343, 91 + 80 * i, fuel_prices[i], ILI9488.BLACK, 2, RGB(140, 240, 140), 6)
        
        self.display.set_font(self.ili_font)