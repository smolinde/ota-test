import machine, os, tarfile, hashlib, json, shutil
import urequests as requests

OTA_API_URL = "https://api.github.com/repos/smolinde/ota-test/releases/latest"

class UpdateManager:

    def __init__(self):
        pass

    def update_available(self):
        current_version = "v0.0.0"
        try:
            with open("version", "r") as f:
                current_version = f.read().strip()
        except:
            with open("version", "w") as f:
                f.write("v0.0.0")

        try:
            response = requests.get(OTA_API_URL)
            data = response.json()
            response.close()
            return current_version, str(data["tag_name"])
        except:
            return None, None

    def download_update(self):
        try:
            os.mkdir("updates")
        except:
            raise Exception("Failed to create updates folder!")

        try:
            response = requests.get(OTA_API_URL)
            data = response.json()
            response.close()
            for asset in data["assets"]:
                if asset["name"].endswith('.tar.gz') or asset["name"].endswith('.sha256'):
                    response = requests.get(asset["browser_download_url"])
                    with open("/updates/"+{asset["name"]}, "wb") as f:
                        f.write(response.content)
                    response.close()

            return "OK", None

        except:
            return "2601", [
                "Update Download Failed!",
                "Something went wrong while downloading",
                "the update. The system will attempt to",
                "download the update in 24 hours again!"]

    def verify_update(self):
        files = os.listdir("updates")
        sha_path = next(("updates/" + f for f in files if f.endswith(".sha256")), None)
        tar_path = next(("updates/" + f for f in files if f.endswith(".tar.gz")), None)
        if not sha_path or not tar_path:
            raise Exception("Missing update files!")

        with open(sha_path, 'r') as f:
            expected_sha = f.read().split()[0]

        sha256 = hashlib.sha256()
        with open(tar_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        if sha256.hexdigest() != expected_sha:
            raise Exception("Update verification failed!")
        

def main():
    update_file = None
    for entry in os.listdir("/"):
        if entry in ["lib", "updates", "main.py"]:
            continue

        try:
            if os.stat("/" + entry)[0] & 0x4000:
                shutil.rmtree("/" + entry)
            else:
                os.remove("/" + entry)
        except:
            raise Exception("Failed to wipe the root storage!")

    for f in os.listdir("updates"):
        if f.endswith(".tar.gz"):
            update_file = f"/updates/{f}"
            break

    if not update_file:
        raise Exception("No update file found!")
    
    with tarfile.open(update_file, "r:gz") as tar:
        members = tar.getmembers()
        for member in members:
            target_path = member.name
            parent_dir = "/".join(target_path.split("/")[:-1])
            if parent_dir and not os.path.exists(parent_dir):
                parts = parent_dir.split("/")
                for i in range(1, len(parts)+1):
                    subpath = "/".join(parts[:i])
                    if subpath and not os.path.exists(subpath):
                        os.mkdir(subpath)
            f = tar.extractfile(member)
            if f:
                with open(target_path, "wb") as out_f:
                    out_f.write(f.read())
            else:
                if not os.path.exists(target_path):
                    os.mkdir(target_path)
    
    os.remove("main.py")
    os.rename("main_NEW.py", "main.py")
    machine.reset()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        machine.deepsleep()