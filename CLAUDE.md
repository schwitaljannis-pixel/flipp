# FLIPP – Claude Code Regeln
## Diese Datei wird bei jeder Session zuerst gelesen

---

## PROJEKTÜBERSICHT

FLIPP ist eine Luxury Arbitrage Intelligence Platform.
- **Backend:** `server.py` — Flask, Port 3001, curl_cffi für Vinted
- **Frontend:** `index.html` — Vanilla JS, TradingView-Stil, IBM Plex Mono
- **Ziel:** Vinted + eBay + Kleinanzeigen gleichzeitig scannen, Luxusartikel finden

---

## ABSOLUTE REGELN — NIEMALS BRECHEN

### 1. EINE SACHE AUF EINMAL
Jede Aufgabe wird in einzelne Schritte zerlegt.
Pro Nachricht: **ein Schritt, eine Änderung, eine Datei.**
Niemals mehrere Dinge gleichzeitig ändern.

### 2. ZEIGEN BEVOR SPEICHERN
Vor jeder Änderung: den **exakten Code-Block zeigen** der geändert wird.
Dann warten. Erst wenn der Nutzer "ok" / "mach es" sagt → speichern.
Ausnahme: Wenn der Nutzer explizit sagt "direkt speichern".

### 3. NUR GENANNTE DATEIEN ANFASSEN
Wenn die Aufgabe `server.py` betrifft → nur `server.py` ändern.
Wenn die Aufgabe `index.html` betrifft → nur `index.html` ändern.
Niemals beide gleichzeitig ohne explizite Erlaubnis.

### 4. NIEMALS DEN GESAMTEN FILE NEUSCHREIBEN
Kein komplettes Überschreiben von Dateien.
Immer nur die **spezifische Stelle** ändern die gefragt wurde.
Bestehender Code bleibt unangetastet.

### 5. SYNTAX PRÜFEN NACH JEDER ÄNDERUNG
Nach jeder Änderung in server.py:
```bash
python3 -m py_compile server.py && echo "OK"
```
Nach jeder Änderung in index.html prüfen ob alle Funktionen noch vorhanden sind.
Fehler selbst fixen, dann kurz melden was behoben wurde.

---

## KOMMUNIKATION

### Kurz und direkt
- Kein unnötiges Erklären was du tust
- Kein "Gerne helfe ich dir dabei..."
- Direkt zur Änderung kommen
- Wenn etwas unklar ist: **eine** kurze Frage stellen, nicht drei

### Output-Format
Geänderten Code so zeigen:
```
// server.py — Zeile 145, Funktion get_fake_risk()
ALT:
[alter Code]

NEU:
[neuer Code]
```

### Fehler melden
Format: `FEHLER: [was] → BEHOBEN: [wie]`
Keine langen Erklärungen dazu.

---

## TECHNISCHE REGELN

### server.py
- Port immer **3001**
- curl_cffi für Vinted-Requests (impersonate='chrome124')
- Nach jeder Session-Änderung: Health-Endpoint testen
- BRAND_IDS nicht überschreiben — nur ergänzen
- Intelligence System (get_demand, get_fake_risk, get_hot_deal, get_decision) niemals löschen

### index.html
- Font: IBM Plex Mono (Zahlen) + DM Sans (Text)
- Farben: --bg:#08080e, --ac:#00d4aa, --red:#ff4d6d
- Niemals das CSS-System ändern ohne explizite Erlaubnis
- Brand-Filter in doScan() niemals entfernen
- calcProfit(), openModal(), buildCard() sind Kern-Funktionen — nicht anfassen

### Git
- Nach jeder fertigen Session: Änderungen zu GitHub pushen
- Repo: `schwitaljannis-pixel/flipp`
- Commit-Message: kurz beschreiben was geändert wurde

---

## SESSION-START RITUAL

Am Anfang jeder neuen Session:
1. Diese Datei lesen
2. `ls` ausführen — alle Dateien anzeigen
3. Kurz bestätigen: "Bereit. [X] Dateien gefunden. Was als nächstes?"
4. Warten auf Aufgabe

---

## AKTUELLE ARCHITEKTUR (Stand: Juni 2026)

```
server.py v4.2
├── Session System     → _vinted_build_session() mit 3 Retries
├── Brand-Lookup       → _vinted_brand_id() dynamisch via /api/v2/brands
├── Fetch Vinted       → search_text='' wenn brand_id gefunden
├── Fetch eBay         → fetch_ebay_listings() + fetch_ebay_sold_price()
├── Fetch Kleinanz.    → fetch_kleinanzeigen() via curl_cffi
├── Normalizer         → normalize_item() für alle Plattformen
├── Intelligence       → get_demand(), get_fake_risk(), get_hot_deal(), get_decision()
└── API Endpoints      → /api/search, /api/health, /api/marketprice, /api/ebay-sold

index.html v4
├── Scanner Tab        → doScan() mit Brand-Filter, 20s Auto-Refresh
├── For You Tab        → renderFy() personalisierter Feed
├── Portfolio Tab      → renderPort() mit CSV Export
├── Settings Tab       → Backend URL, eBay API, Telegram, Gebühren
├── Modal              → openModal() mit Foto-Galerie
└── Intelligence UI    → Demand, Fake Risk, Decision auf jeder Card
```

---

## WAS ALS NÄCHSTES KOMMT

1. eBay Sold Prices → echte Marktpreise statt Schätzungen
2. Seller Score verbessern → Anzahl Bewertungen einberechnen
3. Fake Risk neu kalibrieren → mit echten Preisen
4. Luxury Reference Database → auth_reference.json
5. Telegram Backend Alerts → in server.py, nicht nur Frontend

---

## WICHTIGSTE REGEL

Wenn du dir nicht 100% sicher bist was gemeint ist:
**Frage. Mach nicht einfach irgendwas.**
Eine falsche Änderung kostet mehr Zeit als eine kurze Rückfrage.
