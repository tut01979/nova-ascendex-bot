from fastapi import FastAPI, Request
from pydantic import BaseModel
import ccxt.async_support as ccxt
import asyncio
import os
from datetime import datetime
import urllib.parse
import json

app = FastAPI(title="Nova + Ascendex Bot - OPERANDO 24/7")

# === ASCENDEX CONFIG ===
exchange = ccxt.ascendex({
    'apiKey': os.getenv("ASCENDEX_API_KEY"),
    'secret': os.getenv("ASCENDEX_SECRET"),
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# === MODELO DE SEÑAL (exactamente como lo necesitas) ===
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

# === RUTA PRINCIPAL ===
@app.get("/")
async def home():
    return {
        "status": "NOVA ASCENDEX BOT 100% ACTIVO",
        "hora": datetime.now().isoformat()
    }

# === WEBHOOK PRINCIPAL - ACEPTA TODO LO QUE TRADINGVIEW MANDE ===
@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Leer el cuerpo crudo
        raw_body = await request.body()
        body_text = raw_body.decode("utf-8")

        # Caso 1: TradingView envía message={...}
        if body_text.startswith("message="):
            json_str = body_text[8:]  # quitar "message="
            json_str = urllib.parse.unquote(json_str)
            payload = json.loads(json_str)
        else:
            # Caso 2: JSON directo (por si acaso)
            payload = await request.json()

        # Crear el objeto Signal (ahora sí funciona)
        signal = Signal(**payload)

        print(f"\n[{datetime.now()}] SEÑAL RECIBIDA → {signal.orderId}")
        print(f"Acción: {signal.action} | Cantidad: {signal.quantity} | Precio: {signal.price}")
        print(f"SL: {signal.stop_loss} | TP: {signal.take_profit}")

        # Ejecutar en AscendEx
        side = "buy" if signal.action == "BUY" else "sell"
        symbol = signal.symbol.replace("USDT", "/USDT:USDT")

        # Orden principal (market)
        order = await exchange.create_market_order(symbol, side, float(signal.quantity))
        print(f"ORDEN EJECUTADA → ID: {order['id']}")

        # Stop Loss
        if signal.stop_loss:
            await exchange.create_stop_order(
                symbol,
                "sell" if side == "buy" else "buy",
                float(signal.quantity),
                None,
                {"stopPrice": signal.stop_loss}
            )
            print(f"Stop Loss colocado en {signal.stop_loss}")

        # Take Profit
        if signal.take_profit:
            await exchange.create_limit_order(
                symbol,
                "sell" if side == "buy" else "buy",
                float(signal.quantity),
                signal.take_profit
            )
            print(f"Take Profit colocado en {signal.take_profit}")

        return {
            "status": "EJECUTADO CORRECTAMENTE",
            "orderId": signal.orderId,
            "exchange_order_id": order['id'],
            "hora": datetime.now().isoformat()
        }

    except Exception as e:
        printprix(f"ERROR CRÍTICO: {e}")
        return {
            "status": "ERROR",
            "detalle": str(e)
        }