# Telegram Flight Price Bot ✈️

Este bot monitorea vuelos y permite configurar origen, destino y fechas a través de Telegram. Revisa el mercado cada 6 horas y te notifica sobre las mejores opciones disponibles.

---

## 📹 Demo

<div align="center">
  <a href="https://drive.google.com/file/d/1vKvdgC1G1WZqy8R9UviH2gxbh__vcV_o/view?usp=share_link" target="_blank">
    <img src="https://img.icons8.com/clouds/500/video-playlist.png" alt="Ver demo del bot" width="300"/>
  </a>
</div>

👉 [Haz clic aquí para ver la demo del bot en acción](https://drive.google.com/file/d/1vKvdgC1G1WZqy8R9UviH2gxbh__vcV_o/view?usp=share_link)

---

## Cómo usar

1. Clona el repositorio:
```bash
git clone https://github.com/tu_usuario/flight-price-bot.git
cd flight-price-bot
```

2. Crea tu entorno virtual y activa:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala dependencias:
```bash
pip install -r requirements.txt
```

4. Agrega tu archivo `.env` con tu TOKEN de Telegram:
```env
TELEGRAM_BOT_TOKEN=TU_TOKEN_AQUÍ
```

5. Ejecuta el bot:
```bash
python telegram_bot.py
```

---

## ☁️ Despliegue

Puedes subir este bot a:
- [Replit](https://replit.com) (con UptimeRobot para mantenerlo activo)
- [Render](https://render.com)

---

## 🔁 Funcionalidades

- Consulta vuelos desde Telegram
- Revisión automática cada 6 horas
- Notificaciones inteligentes
- Configura origen, destino, fechas y ventana de búsqueda
