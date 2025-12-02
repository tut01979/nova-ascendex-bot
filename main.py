from fastapi import FastAPI, Request
from pydantic import BaseModel
import ccxt.async_support as ccxt
import os
from datetime import datetime
import json

app = FastAPI(title="Nova + Ascendex Bot - OPERANDO 24/7")

exchange = ccxt.ascendex({
    'apiKey': os.getenv("ASCENDEX_API_KEY"),
    'secret': os.getenv("ASCENDEX_SECRET"),
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}  # swap = futuros perpetuos en Ascendex
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
    orderId: str = None
    timestamp: str = None

@app.get("/")
async def home():
    return {"status": "NOVA ASCENDEX BOT 100% ACTIVO", "hora": datetime.now().isoformat()}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        raw_body = await request.body()
        body_text = raw_body.decode("utf-8").strip()
        
        print(f"RAW recibido ({len(body_text)} chars): {body_text[:500]}")

        # TradingView ahora envía JSON directo → lo intentamos parsear directamente
        payload = json.loads(body_text)
        
        # Pequeño fix por si Ascendex usa SOL/USDT en vez de SOLUSDT
        symbol = payload["symbol"]
        if symbol.endswith("USDT"):
            symbol = symbol.replace("USDT", "/USDT:USDT")

        signal = Signal(**payload)

        print(f"\n[{datetime.now()}] SEÑAL → {signal.action.upper()} {signal.quantity} {signal.symbol} @ {signal.price}")
        print(f"SL: {signal.stop_loss} | TP: {signal.take_profit} | ID: {signal.orderId}")

        side = "buy" if signal.action.lower() == "buy" else "sell"

        # Orden principal al mercado
        order = await exchange.create_market_order(symbol, side, float(signal.quantity))
        print(f"ORDEN EJECUTADA → {order['id']}")

        # Stop-loss (si existe)
        if signal.stop_loss:
            sl_side = "sell" if side == "buy" else "buy"
            await exchange.create_order(symbol, "stop", sl_side, float(signal.quantity), None, {"stopPrice": signal.stop_loss})
            print(f"STOP-LOSS colocado en {signal.stop_loss}")

        # Take-profit (limit normal)
        if signal.take_profit:
            tp_side = "sell" if side == "buy" else "buy"
            await exchange.create_limit_order(symbol, tp_side, float(signal.quantity), signal.take_profit)
            print(f"TAKE-PROFIT colocado en {signal.take_profit}")

        return {"status": "EJECUTADO", "order_id": order['id']}

    except Exception as e:
        print(f"ERROR → {e}")
        return {"status": "ERROR", "msg": str(e)}, 400