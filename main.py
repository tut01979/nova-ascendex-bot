from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
from datetime import datetime

app = FastAPI(title="Nova + Ascendex Bot")

@app.get("/")
def home():
    return {"mensaje": "Nova Trading Bot ONLINE - Listo para recibir señales de TradingView"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print(f"\n[{datetime.now()}] WEBHOOK RECIBIDO:")
    print(data)
    
    return {"status": "recibido", "orderId": data.get("orderId", "sin-id")}