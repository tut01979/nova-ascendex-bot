from fastapi import FastAPI, Request
from pydantic import BaseModel
import ccxt.async_support as ccxt
import os
import json

app = FastAPI(title="Nova Kraken Futures Bot - OPERANDO")

exchange = ccxt.krakenfutures({
    'apiKey': os.getenv("KRAKEN_API_KEY"),
    'secret': os.getenv("KRAKEN_SECRET"),
    'enableRateLimit': True,
})

class Signal(BaseModel):
    action: str
    symbol: str
    quantity: str
    price: float
    stop_loss: float = None
    take_profit: float = None
    exchange: str
    market: str

@app.get("/")
async def home():
    return {"status": "NOVA KRAKEN FUTURES - ACTIVO 24/7"}

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
        # Kraken usa SOLUSD, BTCUSD, etc.
        kraken_symbol = signal.symbol.replace("-PERP", "USD")  # SOL-PERP → SOLUSD

        order = await exchange.create_market_order(kraken_symbol, side, float(signal.quantity))
        print(f"ORDEN EJECUTADA → {order['id']}")

        if signal.stop_loss:
            sl_side = "sell" if side == "buy" else "buy"
            await exchange.create_order(kraken_symbol, "stop", sl_side, float(signal.quantity), None, {"stopPrice": signal.stop_loss})
            print(f"STOP-LOSS colocado en {signal.stop_loss}")

        if signal.take_profit:
            tp_side = "sell" if side == "buy" else "buy"
            await exchange.create_limit_order(kraken_symbol, tp_side, float(signal.quantity), signal.take_profit)
            print(f"TAKE-PROFIT colocado en {signal.take_profit}")

        return {"status": "OK", "order_id": order['id']}

    except Exception as e:
        print(f"ERROR → {e}")
        return {"error": str(e)}, 400