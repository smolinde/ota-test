import urequests as requests

class StationManager:
    __STATION_STATUSES = {
        "open": "OPEN",
        "closed": "CLOSED",
        "no prices": "NO PRICES",
        None: "STATUS UNKNOWN"
    }
    
    def __init__(self, station_ids, fuel_type, api_key):
        self.station_ids = station_ids
        self.fuel_type = fuel_type
        self.base_url_station_info = f"https://creativecommons.tankerkoenig.de/json/prices.php?apikey={api_key}"
    
    def __get_station_status(self, data, station_id):
        try:
            data = data["prices"][station_id]["status"]
            return self.__STATION_STATUSES.get(data)

        except Exception:
            return self.__STATION_STATUSES.get(None)

    def __get_station_fuel_price(self, data, station_id):
        try:
            data = data["prices"][station_id][self.fuel_type]
            return f"{data:.2f}".replace(".", ",") if data is not None else "-,--"

        except Exception:
            return "-,--"
        
    def get_station_data(self):
        try:
            response = requests.get(f"{self.base_url_station_info}&ids={",".join(self.station_ids)}")
            data = response.json()
            response.close()
            statuses = [self.__get_station_status(data, sid) for sid in self.station_ids]
            prices = [self.__get_station_fuel_price(data, sid) for sid in self.station_ids]

        except Exception:
            statuses = [self.__STATION_STATUSES.get(None)] * len(self.station_ids)
            prices = ["-,--"] * len(self.station_ids)

        return statuses, prices