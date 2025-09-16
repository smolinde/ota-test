import ntptime, time

class TimeManager:

    __WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

    def __init__(self):
        self.tz_offset = 0
        self.synced = False

    def sync_time(self):
        try:
            ntptime.settime()  # sets RTC to UTC
            return "OK", None
        except Exception as e:
            print(e)
            return "2501", ["Time synchronization failed!",
                            "This error is caused by the NTP server,",
                            "probably due to a server outage.",
                            "System will attempt to sync again."]

    def set_timezone(self, offset):
        self.tz_offset = offset

    def get_timestamp(self):
        return time.gmtime()
    
    def __get_localtime(self):
        t = time.time() + self.tz_offset * 3600
        return time.localtime(t)
    
    def __last_sunday(self, year, month):
            d = 31
            while True:
                try:
                    tm = time.localtime(time.mktime((year, month, d, 0, 0, 0, 0, 0)))
                    break
                except OverflowError:
                    d -= 1

            while True:
                tm = time.localtime(time.mktime((year, month, d, 0, 0, 0, 0, 0)))
                if tm[6] == 6:  # Sunday
                    return d
                d -= 1
    
    def get_timedate(self):
        t = self.__get_localtime()
        return [
            self.__WEEKDAYS[t[6]],
            "{:02d}.{:02d}.{:04d}".format(t[2], t[1], t[0]),
            "{:02d}:{:02d}".format(t[3], t[4])
        ]

    def get_timezone_de(self) -> int:
        """
        Returns the current timezone offset for Germany (CET=1 or CEST=2).
        Uses European DST rules (last Sunday in March -> last Sunday in October).
        """
        t = self.__get_localtime()
        year, month, day, hour = t[0], t[1], t[2], t[3]

        # Last Sundays
        march_last_sun = self.__last_sunday(year, 3)
        oct_last_sun = self.__last_sunday(year, 10)

        # DST starts: last Sunday in March at 02:00
        if (month > 3 and month < 10):
            return 2  # Summer time
        elif month == 3:
            if day > march_last_sun or (day == march_last_sun and hour >= 2):
                return 2
            else:
                return 1
        elif month == 10:
            if day < oct_last_sun or (day == oct_last_sun and hour < 3):
                return 2
            else:
                return 1
        else:
            return 1  # Winter time
