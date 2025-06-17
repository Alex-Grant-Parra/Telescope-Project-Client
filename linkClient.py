import asyncio
import websockets
import ujson as json  # Using ujson for faster serialization
from cameraController import Camera
import time

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

function_map = {
    "get_temperature": get_temperature,
    "echo": echo,
    "add": add,
    "getCameraChoices":get_camera_choices,
    "setCameraSetting":setCameraSetting,
    
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
