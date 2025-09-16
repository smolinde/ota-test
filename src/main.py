import os, machine, network, time, shutil
from updater import UpdateManager

SSID = 'Wlan-Name'
PASSWORD = 'Wlan-Password'

upmr = UpdateManager()

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print('Connected to WiFi')

def main():
    try:
        shutil.rmtree("updates")
    except OSError:
        pass

    print("This program does A!")
    current_version, update_version = upmr.update_available()
    if current_version != update_version:
        print("Update found!")
        print("Current version:", current_version)
        print("Update version:", update_version)
        print("Downloading update...")
        error_code, error_msg = upmr.download_update()
        if error_code is not "OK":
            print(error_msg)
            machine.reset()
        
        upmr.verify_update()
        os.rename("main.py", "main_OLD.py")
        os.rename("updater.py", "main.py")
        machine.reset()

    else:
        print("Everything is up-to-date!")

if __name__ == '__main__':
    main()