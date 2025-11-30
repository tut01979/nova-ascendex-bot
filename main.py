from fastapi import FastAPI, Request
from pydantic import BaseModel
import ccxt.async_support as ccxt
import os
from datetime import datetime
import urllib.parse
import json

app = FastAPI(title="Nova + Ascendex Bot - OPERANDO 24/7")

exchange = ccxt.ascendex({
    'apiKey': os.getenv("ASCENDEX_API_KEY"),
    'secret': os.getenv("ASCENDEX_SECRET"),
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

class Signal(BaseModel):
    exchange: str
    symbol: str
    market: str
    action: str
    price: str
    quantity: str
    stop_loss: float = None
    take_profit: float = None
    orderId: str
    timestamp: str

@app.get("/")
async def home():
    return {"status": "NOVA ASCENDEX BOT 100% ACTIVO", "hora": datetime.now().isoformat()}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        raw_body = await request.body()
        body_text = raw_body.decode("utf-8").strip()

        print(f"RAW recibido: {body_text[:200]}")  # <-- para ver exactamente qué llega

        # Caso TradingView: message={....}
        if body_text.startswith("message="):
            json_str = body_text[8:]
            json_str = urllib.parse.unquote(json_str)
            payload = json.loads(json_str)
        else:
            # Caso JSON directo o cualquier otra cosa
            payload = json.loads(body_text) if body_text else {}

        signal = Signal(**payload)

        print(f"\n[{datetime.now()}] SEÑAL RECIBIDA → {signal.orderId}")
        print(f"→ {signal.action} {signal.quantity} {signal.symbol} @ {signal.price}")

        side = "buy" if signal.action == "BUY" else "sell"
        symbol = signal.symbol.replace("USDT", "/USDT:USDT")

        order = await exchange.create_market_order(symbol, side, float(signal.quantity))
        print(f"ORDEN EJECUTADA → {order['id']}")

        if signal.stop_loss:
            await exchange.create_stop_order(symbol, "sell" if side == "buy" else "buy",
                                           float(signal.quantity), None, {"stopPrice": signal.stop_loss})
            print(f"SL colocado en {signal.stop_loss}")

        if signal.take_profit:
            await exchange.create_limit_order(symbol, "sell" if side == "buy" else "buy",
                                            float(signal.quantity), signal.take_profit)
            print(f"TP colocado en {signal.take_profit}")

        return {"status": "EJECUTADO", "order_id": order['id']}

    except Exception as e:
        print(f"ERROR → {e}")   # <-- aquí estaba el puto printprix
        return {"status": "ERROR", "msg": str(e)}