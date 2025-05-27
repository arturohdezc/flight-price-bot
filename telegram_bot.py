import os
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import sys

# --- Configuración y log ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
AUTHORIZED_CHAT_ID = int(os.getenv("AUTHORIZED_CHAT_ID", "0"))

print(f"✅ TOKEN cargado: {bool(TELEGRAM_TOKEN)}")
print(f"✅ API_KEY Amadeus cargado: {bool(AMADEUS_API_KEY)}")

user_config = {}

# --- Decorador para acceso autorizado ---
def authorized_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if AUTHORIZED_CHAT_ID and chat_id != AUTHORIZED_CHAT_ID:
            await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
            return
        return await func(update, context)
    return wrapper

# --- Utilidades de Amadeus ---
def get_token():
    response = requests.post(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": AMADEUS_API_KEY,
            "client_secret": AMADEUS_API_SECRET
        }
    )
    return response.json()["access_token"]

def mostrar_oferta(oferta):
    salida = []

    for i, itinerario in enumerate(oferta["itineraries"]):
        tipo = "IDA" if i == 0 else "VUELTA"
        segmentos = itinerario["segments"]
        num_stops = len(segmentos) - 1
        duracion = itinerario["duration"].replace("PT", "").lower()

        salida.append(f"🟢 ALERTA DE PRECIO ({tipo})")

        for seg in segmentos:
            carrier = seg["carrierCode"]
            flight_number = seg["number"]
            origin = seg["departure"]["iataCode"]
            destination = seg["arrival"]["iataCode"]
            departure_fmt = seg["departure"]["at"]
            arrival_fmt = seg["arrival"]["at"]

            salida.append(
                f"✈️  Ruta: {origin} → {destination}\n"
                f"🛫 Aerolínea: {carrier} - Vuelo {flight_number}\n"
                f"🕐 Salida: {departure_fmt}\n"
                f"🕐 Llegada: {arrival_fmt}\n"
            )

        salida.append(f"⏱️  Duración total: {duracion}")
        salida.append(f"🔁 Escalas: {num_stops}\n")

    precio = oferta["price"]["total"]
    moneda = oferta["price"]["currency"]
    clase = oferta["travelerPricings"][0]["fareDetailsBySegment"][0]["cabin"]
    maletas = oferta["travelerPricings"][0]["fareDetailsBySegment"][0]["includedCheckedBags"]["quantity"]

    salida.append(f"🪑 Clase: {clase} | 🧳 Maletas incluidas: {maletas}")
    salida.append(f"💰 Precio total: {precio} {moneda}")

    return "\n".join(salida)

def buscar_vuelo(conf):
    token = get_token()
    f = datetime.strptime(conf["date"], "%Y-%m-%d")
    ida = (f - timedelta(days=int(conf["window"]))).strftime("%Y-%m-%d")
    vuelta = (f + timedelta(days=int(conf["window"]))).strftime("%Y-%m-%d")
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "originLocationCode": conf["origin"],
        "destinationLocationCode": conf["destination"],
        "departureDate": ida,
        "returnDate": vuelta,
        "adults": 1,
        "currencyCode": "USD",
        "max": 5
    }

    logger.info(f"📤 Enviando búsqueda con parámetros: {params}")
    response = requests.get("https://test.api.amadeus.com/v2/shopping/flight-offers", headers=headers, params=params)
    data = response.json()
    logger.info(f"📥 Respuesta Amadeus: {data}")

    if not data.get("data"):
        return "❌ No se encontraron vuelos."
    mejor = min(data["data"], key=lambda x: float(x["price"]["total"]))
    return mostrar_oferta(mejor)

# --- Comandos Telegram ---
@authorized_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    print(f'🟢 Usuario {uid} ejecutó /start')
    user_config[uid] = {
        "origin": "LAX",
        "destination": "CDG",
        "date": "2025-10-26",
        "window": 3
    }
    await update.message.reply_text(
        "✈️ Bot activado. Usa /search para buscar vuelos.\n"
        "Comandos disponibles:\n"
        "/set_origin XXX\n"
        "/set_destination XXX\n"
        "/set_date YYYY-MM-DD\n"
        "/set_window N\n"
        "/status\n"
        "/stop"
    )

@authorized_only
async def set_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_config:
        await update.message.reply_text("⚠️ Usa /start primero.")
        return
    user_config[uid]["origin"] = context.args[0].upper()
    await update.message.reply_text(f"✅ Origen actualizado a {context.args[0].upper()}")

@authorized_only
async def set_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_config:
        await update.message.reply_text("⚠️ Usa /start primero.")
        return
    user_config[uid]["destination"] = context.args[0].upper()
    await update.message.reply_text(f"✅ Destino actualizado a {context.args[0].upper()}")

@authorized_only
async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_config:
        await update.message.reply_text("⚠️ Usa /start primero.")
        return
    user_config[uid]["date"] = context.args[0]
    await update.message.reply_text(f"✅ Fecha actualizada a {context.args[0]}")

@authorized_only
async def set_window(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_config:
        await update.message.reply_text("⚠️ Usa /start primero.")
        return
    user_config[uid]["window"] = int(context.args[0])
    await update.message.reply_text(f"✅ Ventana de búsqueda actualizada a {context.args[0]} días")

@authorized_only
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conf = user_config.get(update.effective_user.id)
    if not conf:
        await update.message.reply_text("⚠️ No hay configuración activa. Usa /start primero.")
        return
    msg = (
        "📊 Parámetros actuales:\n"
        f"• Origen: {conf['origin']}\n"
        f"• Destino: {conf['destination']}\n"
        f"• Fecha: {conf['date']}\n"
        f"• Ventana: ±{conf['window']} días"
    )
    await update.message.reply_text(msg)

@authorized_only
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_config:
        del user_config[uid]
        await update.message.reply_text("🛑 Bot detenido y configuración borrada.")
    else:
        await update.message.reply_text("ℹ️ No había ninguna configuración activa.")

@authorized_only
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conf = user_config.get(update.effective_user.id)
    if not conf:
        await update.message.reply_text("⚠️ Primero ejecuta /start para iniciar.")
        return

    logger.info(f"🔍 Ejecutando búsqueda con configuración: {conf}")
    await update.message.reply_text("🔍 Buscando vuelos...")

    try:
        resultado = buscar_vuelo(conf)
        await update.message.reply_text(resultado)
    except Exception as e:
        logger.error(f"❌ Error en búsqueda de vuelos: {e}")
        await update.message.reply_text("❌ Ocurrió un error al buscar vuelos.")

# --- Inicialización del bot ---
async def main():
    print("🔄 Inicializando ApplicationBuilder...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    print("✅ Application construida. Registrando handlers...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_origin", set_origin))
    app.add_handler(CommandHandler("set_destination", set_destination))
    app.add_handler(CommandHandler("set_date", set_date))
    app.add_handler(CommandHandler("set_window", set_window))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))

    print("🔧 Todos los handlers registrados.")
    logger.info("✈️ Bot ejecutándose...")
    print("🚦 Lanzando polling...")

    await app.run_polling()

# --- Compatibilidad con macOS / notebooks ---
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
