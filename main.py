from fastapi import FastAPI, Request
from pydantic import BaseModel
import ccxt.async_support as ccxt
import os
from datetime import datetime
import json

app = FastAPI()

exchange = ccxt.ascendex({
    'apiKey': os.getenv("ASCENDEX_API_KEY"),
    'secret': os.getenv("ASCENDEX_SECRET"),
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}  # swap = futuros perpetuos
})

class Signal(BaseModel):
    action: str
    symbol: str
    quantity: str
    price: float                # ← float, no string
    stop_loss: float = None
    take_profit: float = None
    exchange: str
    market: str
    orderId: str = None         # ← opcional
    timestamp: str = None       # ← opcional

@app.get("/")
async def home():
    return {"status": "NOVA ASCENDEX BOT 100% ACTIVO"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        raw = await request.body()
        data = raw.decode("utf-8").strip()
        print(f"RAW recibido: {data}")

        payload = json.loads(data)
        signal = Signal(**payload)

        print(f"SEÑAL → {signal.action.upper()} {signal.quantity} {signal.symbol} @ {signal.price}")

        side = "buy" if signal.action == "buy" else "sell"

        order = await exchange.create_market_order(signal.symbol, side, float(signal.quantity))
        print(f"ORDEN EJECUTADA → {order['id']}")

        if signal.stop_loss:
            sl_side = "sell" if side == "buy" else "buy"
            await exchange.create_order(signal.symbol, "stop", sl_side, float(signal.quantity), None, {"stopPrice": signal.stop_loss})
            print(f"SL colocado en {signal.stop_loss}")

        if signal.take_profit:
            tp_side = "sell" if side == "buy" else "buy"
            await exchange.create_limit_order(signal.symbol, tp_side, float(signal.quantity), signal.take_profit)
            print(f"TP colocado en {signal.take_profit}")

        return {"status": "OK", "order_id": order['id']}

    except Exception as e:
        print(f"ERROR → {e}")
        return {"error": str(e)}, 400