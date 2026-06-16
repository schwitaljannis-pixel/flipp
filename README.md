# FLIPP – Luxury Arbitrage Intelligence Platform

Ein KI-gestütztes Tool für Luxury Reselling Arbitrage.
Scannt Vinted, eBay und Kleinanzeigen gleichzeitig.

## Stack
- Backend: Python Flask + curl_cffi
- Frontend: Vanilla HTML/CSS/JS (TradingView-Stil)

## Start
```bash
pip install flask requests curl_cffi
python3 server.py
```

Dann `index.html` im Browser öffnen.

## Features
- Multi-Platform Scanner (Vinted + eBay + Kleinanzeigen)
- Präzise Brand-ID Suche (exakt wie Vinted selbst)
- Intelligence System: Demand Score, Fake Risk, BUY NOW / CHECK FIRST / SKIP
- Portfolio Tracking mit CSV Export
- Telegram Alerts für ULTRA DEALS
- For You Feed (personalisiert)
