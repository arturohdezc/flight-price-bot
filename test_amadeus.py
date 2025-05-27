#!/usr/bin/env python3
"""
test_amadeus_auth.py

Este script prueba si tu API Key y Secret de Amadeus funcionan,
haciendo una autenticación directa contra el endpoint oficial.

No requiere la librería `amadeus`, solo `requests` y `python-dotenv`.

Instalación: pip install requests python-dotenv
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# ================================
# Cargar .env con ruta absoluta
# ================================
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Obtener las credenciales del archivo .env
API_KEY = os.getenv("AMADEUS_API_KEY")
API_SECRET = os.getenv("AMADEUS_API_SECRET")

print("API Key:", repr(API_KEY))
print("API Secret:", repr(API_SECRET))

if not API_KEY or not API_SECRET:
    print("❌ No se encontraron las credenciales en .env")
    exit(1)

# ================================
# Solicitar token a Amadeus
# ================================
url = "https://test.api.amadeus.com/v1/security/oauth2/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "grant_type": "client_credentials",
    "client_id": API_KEY,
    "client_secret": API_SECRET
}

try:
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    token_info = response.json()

    print("\n✅ Token obtenido correctamente:")
    print(f"Access Token: {token_info['access_token']}")
    print(f"Expira en: {token_info['expires_in']} segundos")
except requests.exceptions.HTTPError as http_err:
    print(f"\n❌ Error HTTP {response.status_code}")
    print(response.text)
except Exception as err:
    print(f"\n❌ Error inesperado: {err}")
