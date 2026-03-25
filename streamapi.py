#get data from an API / file / stream
#Simplest version: polling an API
import requests
import time
import pandas as pd
from datetime import datetime

rows = []

url = "https://api.coingecko.com/api/v3/simple/price"
params = {"ids": "bitcoin", "vs_currencies": "usd"}

while True:
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    rows.append({
        "timestamp": datetime.utcnow(),
        "type": "btc_price",
        "value": data["bitcoin"]["usd"]
    })

    df = pd.DataFrame(rows)
    print(df.tail())

    time.sleep(2)


#Streaming with Server-Sent Events (SSE)

import requests
import json

url = "https://example.com/events"

with requests.get(url, stream=True) as r:
    r.raise_for_status()

    for line in r.iter_lines():
        if line:
            decoded = line.decode("utf-8")

            if decoded.startswith("data:"):
                payload = decoded.replace("data:", "", 1).strip()
                event = json.loads(payload)
                print(event)


#Streaming with WebSocket
import asyncio
import json
import websockets

async def consume():
    url = "wss://example.com/stream"

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"action": "subscribe", "topic": "events"}))

        while True:
            message = await ws.recv()
            event = json.loads(message)
            print(event)

asyncio.run(consume())

#Chunked HTTP / line-delimited JSON
import requests
import json

url = "https://example.com/stream-json"

with requests.get(url, stream=True) as r:
    r.raise_for_status()

    for line in r.iter_lines():
        if line:
            obj = json.loads(line.decode("utf-8"))
            print(obj)
