import network, time, socket

class WlanManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.was_connected_before = False
        if self.wlan.active():
            self.wlan.active(False)
            time.sleep(5)
        
        self.wlan.active(True)

    def connect(self, ssid, psk):
        if self.wlan.isconnected():
            return

        self.wlan.connect(ssid, psk)

    def is_connected_boolean(self):
        if self.wlan.isconnected():
            return True
        else:
            return False

    def is_connected(self):
        if self.wlan.isconnected():
            self.was_connected_before = True
            return "OK", None
        elif self.was_connected_before:
            return "2302", ["Connection to the WLAN lost!",
                            "Please make sure that your WLAN is in",
                            "a close enough range for stable",
                            "operation. Trying to reconnect soon."]
        else:
            return "2301", ["Connecting to the WLAN failed!",
                            "Please make sure that your WLAN is in",
                            "range, your SSID and PSK are correct,",
                            "and the router operates at 2.4GHz!"]

    def get_ip(self):
        return self.wlan.ifconfig()[0] if self.wlan.isconnected() else None

    def device_online(self):
        try:
            addr = socket.getaddrinfo("1.1.1.1", 53)[0][-1]
            socket.socket().connect(addr)
            return "OK", None
        
        except Exception as e:
            return "2401", ["No internet conenction!",
                        "Although your WLAN works, there is no",
                        "internet connection. Please restart your",
                        "WLAN router and check for an outage."]
        
    def close(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self.wlan.active(False)