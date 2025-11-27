from fastapi import FastAPI, Request
from pydantic import BaseModel
import ccxt.async_support as ccxt
import asyncio
import os
from datetime import datetime

app = FastAPI(title="Nova + Ascendex Bot - OPERANDO 24/7")

# === ASCENDEX (testnet o real) ===
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
    action: str        # BUY o SELL
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
async def webhook(signal: Signal):
    print(f"\n[{datetime.now()}] SEÑAL RECIBIDA → {signal.orderId}")
    print(signal)

    side = "buy" if signal.action == "BUY" else "sell"
    symbol = signal.symbol.replace("USDT", "/USDT:USDT")  # formato Ascendex

    try:
        # ORDEN PRINCIPAL (market)
        order = await exchange.create_market_order(symbol, side, float(signal.quantity))
        print(f"ORDEN EJECUTADA → ID: {order['id']}")

        # SL y TP si vienen
        if signal.stop_loss:
            await exchange.create_stop_order(symbol, "sell" if side=="buy" else "buy",
                                           float(signal.quantity), None, {"stopPrice": signal.stop_loss})
        if signal.take_profit:
            await exchange.create_limit_order(symbol, "sell" if side=="buy" else "buy",
                                             float(signal.quantity), signal.take_profit)

        return {"status": "EJECUTADO", "orderId": signal.orderId, "exchange_order": order['id']}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"status": "ERROR", "msg": str(e)}