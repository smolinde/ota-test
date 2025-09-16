import os, ure, json, uhashlib
from machine import Pin, SPI
from drivers.sdcard import SDCard
from hashdata import EXPECTED_HASHES

class SDCardManager:
    def __init__(self):
        self.properties = {}
        self.uuid_regex = ure.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
        self.sd = None
        
    def open_sd_card(self):
        try:
            os.listdir("/sd")
            return "OK", None
        except Exception:
            try:
                self.sd = SDCard(SPI(1, baudrate=2000000, sck=Pin(21), mosi=Pin(39), miso=Pin(40)), Pin(38))
                os.mount(self.sd, "/sd")
                if not self.__validate_hashes():
                    return "1102", ["There are missing or corrupted contents",
                                    "on the SD card! Please double-check the",
                                    "SD card for missing folders and files!"]
                return "OK", None

            except Exception:
                return "1101", ["SD Card is missing or has wrong",
                                "format, it should be FAT32 formatted!"]

    def validate_contents(self):
        if "properties.json" not in os.listdir("/sd"):
            return "1103", ["Missing properties.json file!"]
        
        try:
            with open("/sd/properties.json", "r") as f:
                self.properties = json.load(f)
        except Exception:
            return "1104", ["Failed to load properties!",
                            "Something is wrong, please check",
                            "the file contents!"]
        
        if not self.__measure_station_icons():
            return "1105", ["Your custom gas station icons don't match",
                            "the expected size or are formatted",
                            "incorrectly!",
                            "Expected size: 64x64 pixels"]
        
        for name in dir(self):
            if name.startswith("_SDCardManager__check"):
                property_checker = getattr(self, name)
                if callable(property_checker):
                    error_code, error_text = property_checker()
                    if error_code != "OK":
                        return error_code, error_text

        return "OK", None

    def __is_valid_uuid(self, uuid):
        return self.uuid_regex.match(uuid) is not None

    def __sha1sum(self, filepath):
        h = uhashlib.sha1()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                h.update(chunk)
        return h.digest().hex()

    def __validate_hashes(self):
        for filepath, expected in EXPECTED_HASHES.items():
            try:
                actual = self.__sha1sum("/sd/" + filepath)
                if actual != expected:
                    return False
                
            except OSError:
                return False
        
        return True

    def __measure_station_icons(self):
        try:
            files = os.listdir("/sd/icons/station_icons")
        except:
            raise OSError("Folder \'station_icons\' is missing!")

        for f in files:
            if f.endswith(".rgb666"):
                path = "/sd/icons/station_icons/" + f
                try:
                    size = os.stat(path)[6]
                    if size != 64 * 64 * 3:
                        return False
                except:
                    return False
        
        return True
    
    def get_icon(self, icon_type, icon_name):
        if icon_type == "station":
            folder = f"/sd/icons/station_icons"
        elif icon_type == "weather":
            folder = f"/sd/icons/weather_icons"
        elif icon_type == "symbol":
            folder = "/sd/icons/symbols"
        else:
            return None
        
        filename = f"{icon_name}.rgb666"
        fallback = "unknown.rgb666"
        files = os.listdir(folder)
        selected_file = filename if filename in files else fallback

        with open(f"{folder}/{selected_file}", "rb") as f:
            return f.read()
    
    def get_error_qr_code(self, error_code):  
        filename = f"{error_code}.rgb666"
        fallback = "1000.rgb666"
        files = os.listdir("/sd/errors")
        selected_file = filename if filename in files else fallback

        with open(f"/sd/errors/{selected_file}", "rb") as f:
            return f.read()

    def __check_wlan_ssid(self):
        wlan_ssid = self.properties.get("wlan_ssid")
        if isinstance(wlan_ssid, str) and wlan_ssid.strip() and len(wlan_ssid) <= 32:
            return "OK", None
        else:
            return "1201", ["The WLAN SSID is not valid!",
                            "Please provide a valid WLAN SSID in",
                            "the properties.json file!"]

    def __check_wlan_psk(self):
        wlan_psk = self.properties.get("wlan_psk")
        if isinstance(wlan_psk, str) and wlan_psk.strip() and len(wlan_psk) and 8 <= len(wlan_psk) <= 63:
            return "OK", None
        else:
            return "1202", ["The WLAN password is not valid!",
                            "Please provide a valid WLAN password",
                            "in the properties.json file!"]

    def __check_tankerkoenig_api_key(self):
        tankerkoenig_api_key = self.properties.get("tankerkoenig_api_key")
        if isinstance(tankerkoenig_api_key, str) and tankerkoenig_api_key.strip() and self.__is_valid_uuid(tankerkoenig_api_key):
            return "OK", None
        else:
            return "1203", ["The Tankerkoenig API key is not valid!",
                            "Please provide a valid API key in the",
                            "properties.json file!"]

    def __check_station_ids(self):
        station_ids = self.properties.get("station_ids")
        if (
            isinstance(station_ids, list)
            and len(station_ids) == 3
            and all(isinstance(i, str) and self.__is_valid_uuid(i) and i.strip() for i in station_ids)
        ):
            if any(station_ids.count(x) > 1 for x in station_ids):
                return "1205", ["The station ID's are not unique!",
                            "Please provide three unique station ID's",
                            "in the properties.json file!"]
            else:
                return "OK", None
        else:
            return "1204", ["The station ID's are not valid!",
                            "Please provide three valid station ID's",
                            "as a list in the properties.json file!"]
        
    def __check_station_labels(self):
        valid_labels = True
        station_labels = self.properties.get("station_labels")
        if not isinstance(station_labels, list) or len(station_labels) != 3:
            valid_labels = False

        for row in station_labels:
            if not isinstance(row, list) or len(row) != 3:
                valid_labels = False
                break

            for item in row:
                if item is not isinstance(item, str):
                    valid_labels = False
                    break
            
            if not valid_labels:
                break

        if valid_labels:
            return "OK", None
        else:
            return "1206", ["The station labels are not valid!",
                            "Please provide valid station labels as a",
                            "3x3 list in the properties.json file!"]

    def __check_fuel_type(self):
        fuel_type = self.properties.get("fuel_type")
        if fuel_type in ("e5", "e10", "diesel"):
            return "OK", None
        else:
            return "1207", ["The fuel type is not valid!",
                            "Please provide a valid fuel type in",
                            "the properties.json file!",
                            "Valid fuel types: e5, e10, diesel"]

    def __check_weather_lat(self):
        weather_lat = self.properties.get("weather_lat")
        if isinstance(weather_lat, (int, float)) and weather_lat > -90. and weather_lat < 90.:
            return "OK", None
        else:
            return "1208", ["The latitude is not valid!",
                            "Please provide a valid latitude in",
                            "the properties.json file!",
                            "Valid latitudes are between -90 and 90"]

    def __check_weather_long(self):
        weather_long = self.properties.get("weather_long")
        if isinstance(weather_long, (int, float)) and weather_long > -180. and weather_long < 180.:
            return "OK", None
        else:
            return "1209", ["The longitude is not valid!",
                            "Please provide a valid longitude in",
                            "the properties.json file!",
                            "Valid longitudes are between -180 and 180"]

    def get_property_value(self, property_name):
        property = self.properties.get(property_name)
        if property is None:
            return None
        elif isinstance(property, (int, float)):
            return round(float(property), 7)
        else:
            return property

    def close(self):
        try:
            os.umount("/sd")
        except Exception:
            pass