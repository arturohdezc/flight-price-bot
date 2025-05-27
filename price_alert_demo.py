#!/usr/bin/env python3
"""
price_alert_demo.py

Bot que consulta precios de vuelos con Amadeus, cada 6 horas,
y muestra info detallada con horarios, aerolínea, duración y enlace a Google Flights.
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import schedule

# ======================
# Cargar credenciales
# ======================
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("AMADEUS_API_KEY")
API_SECRET = os.getenv("AMADEUS_API_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ Faltan las credenciales en el archivo .env")
    exit(1)

# ======================
# Configuración
# ======================
ORIGIN = "LAX"
DESTINATIONS = ["CDG", "FCO", "MAD", "BCN"]
DEPARTURE_DATE = "2025-09-22"
MAX_PRICE_ALERT = 600  # USD
LOG_FILE = "flight_price_alert.json"
ERROR_LOG = "flight_price_alert.log"
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# Opcional: Diccionario de aerolíneas
AIRLINES = {
    "AC": "Air Canada",
    "IB": "Iberia",
    "AF": "Air France",
    "KL": "KLM",
    "LH": "Lufthansa",
    "AA": "American Airlines",
    "UA": "United",
    "DL": "Delta",
    "GP": "Gambia Bird Airlines"
}

# ======================
# Obtener token
# ======================
def get_access_token():
    try:
        response = requests.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": API_KEY,
                "client_secret": API_SECRET
            }
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as err:
        log_error("AUTH", str(err))
        return None

# ======================
# Consulta de precios
# ======================
def check_prices():
    token = get_access_token()
    if not token:
        print("❌ No se pudo obtener el token.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    for destination in DESTINATIONS:
        params = {
            "originLocationCode": ORIGIN,
            "destinationLocationCode": destination,
            "departureDate": DEPARTURE_DATE,
            "adults": 1,
            "currencyCode": "USD",
            "max": 5
        }

        try:
            response = requests.get(SEARCH_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            offers = data.get('data', [])
            if not offers:
                raise ValueError("No se encontraron precios disponibles")

            best_offer = min(offers, key=lambda x: float(x['price']['total']))
            cheapest_price = float(best_offer['price']['total'])

            carrier = best_offer['validatingAirlineCodes'][0]
            carrier_name = AIRLINES.get(carrier, carrier)
            segments = best_offer['itineraries'][0]['segments']
            origin = segments[0]['departure']['iataCode']
            destination_code = segments[-1]['arrival']['iataCode']
            departure_time = segments[0]['departure']['at']
            arrival_time = segments[-1]['arrival']['at']
            departure_fmt = datetime.fromisoformat(departure_time).strftime("%Y-%m-%d %H:%M")
            arrival_fmt = datetime.fromisoformat(arrival_time).strftime("%Y-%m-%d %H:%M")
            num_stops = len(segments) - 1
            duration = best_offer['itineraries'][0]['duration']
            flight_number = segments[0]['carrierCode'] + segments[0]['number']

            flight_info = {
                "price": cheapest_price,
                "carrier": carrier,
                "origin": origin,
                "destination": destination_code,
                "departure": departure_time,
                "arrival": arrival_time,
                "duration": duration,
                "stops": num_stops,
                "flight_number": flight_number
            }

            log_price(destination, flight_info)

            if cheapest_price < MAX_PRICE_ALERT:
                print(f"""
🟢 ALERTA DE PRECIO
✈️  Ruta: {origin} → {destination_code}
💸 Precio: ${cheapest_price} USD
🛫 Aerolínea: {carrier_name} - Vuelo {flight_number}
🕐 Salida: {departure_fmt}
🕐 Llegada: {arrival_fmt}
⏱️  Duración: {duration.replace('PT', '').lower()}
🔁 Escalas: {num_stops}
🌐 Reserva: https://www.google.com/flights?hl=es#flt={origin}.{destination_code}.{DEPARTURE_DATE}
                """)
            else:
                print(f"🔍 {destination}: ${cheapest_price} USD ({carrier_name})")

        except Exception as err:
            log_error(destination, str(err))
            print(f"❌ Error consultando {destination}: {err}")

# ======================
# Guardar historial
# ======================
def log_price(destination, info):
    timestamp = datetime.now().isoformat()
    entry = {"time": timestamp, **info}

    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {}

        if destination not in data:
            data[destination] = []

        data[destination].append(entry)

        with open(LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        log_error("LOG", f"Error al guardar precio: {e}")

def log_error(source, message):
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{source}] {message}\n"
    with open(ERROR_LOG, "a") as f:
        f.write(log_entry)

# ======================
# Scheduler
# ======================
schedule.every(6).hours.do(check_prices)

print("⏳ Iniciando price_alert_demo...")
check_prices()

while True:
    schedule.run_pending()
    time.sleep(60)
