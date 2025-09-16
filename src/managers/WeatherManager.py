import urequests as requests

class WeatherManager:
    def __init__(self, lat, long):
        self.base_url_current_weather = f"https://api.brightsky.dev/current_weather?lat={lat}&lon={long}"
        self.base_url_weather = f"https://api.brightsky.dev/weather?lat={lat}&lon={long}"

    def __round_half_up(self, x):
            if abs(x)%1<.5:
                return int(x)
            return int(x) + 1 if x > 0 else int(x) - 1

    def __get_current_temperature(self, data):
        try:
            data = data["weather"]["temperature"]
            return f"{self.__round_half_up(data)}`C" if data is not None else "N/A"

        except Exception:
            return "----"
        
    def __get_rain_probability(self, data, hour):
        try:
            data = data["weather"][hour]["precipitation_probability"]
            return f"{data}%" if data is not None else "0%"

        except Exception:
            return "----"
    
    def __get_min_max_temperature(self, data, current_temperature):
        try:
            data = [entry["temperature"] for entry in data["weather"][:24]]
            data = [x for x in data if x is not None]
            if len(data) < 18:
                return "----", "----"
            
            min_temp = self.__round_half_up(min(data))
            max_temp = self.__round_half_up(max(data))
            if current_temperature is not "----":
                current_temperature = int(current_temperature[:-2])
                min_temp = current_temperature if current_temperature < min_temp else min_temp
                max_temp = current_temperature if current_temperature > max_temp else max_temp

            return f"{min_temp}`C", f"{max_temp}`C"

        except Exception:
            return "----", "----"
    
    def __get_weather_icon(self, data):
        try:
            data = data["weather"]["icon"]
            return str(data) if data is not None else "unknown"

        except Exception:
            return "unknown"

    def get_weather_data(self, timestamp):
        date = "{:04d}-{:02d}-{:02d}".format(
            timestamp[0], timestamp[1], timestamp[2]
        )
        try:
            response = requests.get(self.base_url_current_weather)
            data = response.json()
            response.close()
            current_temperature = self.__get_current_temperature(data)
            weather_icon_name = self.__get_weather_icon(data)
        except Exception:
            current_temperature = "----"
            weather_icon_name = "unknown"

        try:
            response = requests.get(f"{self.base_url_weather}&date={date}")
            data = response.json()
            response.close()
            rain_probability = self.__get_rain_probability(data, timestamp[3])
            min, max = self.__get_min_max_temperature(data, current_temperature)
        except Exception:
            rain_probability, min, max = "----"

        return [current_temperature, rain_probability, min, max], weather_icon_name