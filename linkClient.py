import asyncio
import websockets
import json

CLIENT_ID = "pi-001"
SERVER_URI = "ws://82.36.204.156:8001"

# Define functions
def get_temperature():
    return 22.7

def echo(message):
    return f"Echo: {message}"

def add(a, b):
    return float(a) + float(b)

# Function mapping
function_map = {
    "get_temperature": get_temperature,
    "echo": echo,
    "add": add,
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
                response = {"result": result, "id": data.get("id")}
            else:
                response = {"error": f"Function '{function_name}' not found", "id": data.get("id")}

            await ws.send(json.dumps(response))
        except Exception as e:
            await ws.send(json.dumps({"error": str(e)}))

async def run_client():
    async with websockets.connect(SERVER_URI) as ws:
        print(f"[{CLIENT_ID}] Connected to {SERVER_URI}")
        await handle_server(ws)

asyncio.run(run_client())
