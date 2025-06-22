import asyncio
import websockets
import ujson as json  # Using ujson for faster serialization
from cameraController import Camera
import time
import requests
import os

CLIENT_ID = "pi-001"
SERVER_URI = "ws://82.36.204.156:8001"

def get_temperature():
    return 22.7

def echo(message):
    return f"Echo: {message}"

def add(a, b):
    return float(a) + float(b)

def get_camera_choices():
    # Map setting names to gphoto2 config paths
    settings = {
        "shutterSpeed": "/main/capturesettings/shutterspeed",
        "iso": "/main/imgsettings/iso",
        # Add more settings as needed
    }
    choices = {}
    start = time.time()
    for label, path in settings.items():
        result = Camera.getSettingChoices(label, path)
        choices[label] = result if result else []
    print(f"get_camera_choices took {time.time() - start:.2f} seconds")
    return choices

def setCameraSetting(label, value):
    # label, value = listArg[0], listArg[1]
    Camera.setSetting(label, value)
    return f"Set {label} to {value}"

def capturePhoto(currentid):
    files = Camera.capturePhoto(currentid=currentid) # Returns a list of two file names, one raw, one jpeg


    print(files)

    if not isinstance(files, list) or len(files) < 2:
        print("[ERROR] Camera.capturePhoto() did not return two valid files")
        return

    current_dir = os.getcwd()
    photos_dir = os.path.join(current_dir, "photos/default")

    # Ensure directory exists
    if not os.path.exists(photos_dir):
        print(f"[ERROR] Directory '{photos_dir}' does not exist.")
        return

    # Prepare file paths
    files = [os.path.join(photos_dir, file) for file in files]

    # Verify files exist
    missing_files = [file for file in files if not os.path.exists(file)]
    if missing_files:
        print(f"[ERROR] The following files are missing: {missing_files}")
        return
    
    server_url = "http://82.36.204.156:25566/upload"

    file_data = {f"file{index}": open(file, "rb") for index, file in enumerate(files)}

    try:
        print("[DEBUG] Sending files to server...")
        response = requests.post(server_url, files=file_data)
        print("[DEBUG] Server response:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to upload files: {e}")
    finally:
        # Ensure files are closed
        for f in file_data.values():
            f.close()

function_map = {
    "get_temperature": get_temperature,
    "echo": echo,
    "add": add,
    "getCameraChoices":get_camera_choices,
    "setCameraSetting":setCameraSetting,
    "capturePhoto": capturePhoto
}

async def handle_server(ws):
    await ws.send(CLIENT_ID)
    async for message in ws:
        try:
            data = json.loads(message)
            function_name = data.get("function")

            if function_name in function_map:
                func = function_map[function_name]
                args = data.get("args", [])
                result = func(*args)
                response = json.dumps({"result": result, "id": data.get("id")})
            else:
                response = json.dumps({"error": f"Function '{function_name}' not found", "id": data.get("id")})

            await ws.send(response)
        except Exception as e:
            await ws.send(json.dumps({"error": str(e)}))

async def run_client():
    async with websockets.connect(SERVER_URI, ping_interval=20) as ws:
        print(f"[{CLIENT_ID}] Connected to {SERVER_URI}")
        await handle_server(ws)

asyncio.run(run_client())
