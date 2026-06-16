"""
FLIPP v4.1 – Luxury Arbitrage Scanner
=======================================
Multi-Platform: Vinted + eBay + Kleinanzeigen
Start: pip install flask requests curl_cffi && python3 server.py
URL:   http://localhost:3001
"""

from flask import Flask, request, jsonify, send_from_directory
import time, os, random, threading, re
import requests as std_requests

try:
    from curl_cffi import requests as cffi_requests
    _CFFI = True
except ImportError:
    _CFFI = False

app  = Flask(__name__, static_folder='.')
PORT = 3001

@app.after_request
def cors(r):
    r.headers['Access-Control-Allow-Origin']  = '*'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    r.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return r

# ── MARKTPREISE ───────────────────────────────────────────────
MARKET = {
    'hermès':          {'avg': 680,  'min': 280,  'max': 2800},
    'hermes':          {'avg': 680,  'min': 280,  'max': 2800},
    'chanel':          {'avg': 920,  'min': 350,  'max': 3500},
    'louis vuitton':   {'avg': 480,  'min': 180,  'max': 1800},
    'dior':            {'avg': 420,  'min': 150,  'max': 1600},
    'bottega veneta':  {'avg': 520,  'min': 200,  'max': 1900},
    'prada':           {'avg': 340,  'min': 120,  'max': 1200},
    'gucci':           {'avg': 280,  'min': 100,  'max': 950},
    'balenciaga':      {'avg': 340,  'min': 120,  'max': 980},
    'rick owens':      {'avg': 260,  'min': 95,   'max': 850},
    'maison margiela': {'avg': 220,  'min': 85,   'max': 720},
    'chrome hearts':   {'avg': 480,  'min': 180,  'max': 1600},
    'off-white':       {'avg': 260,  'min': 95,   'max': 820},
    'saint laurent':   {'avg': 300,  'min': 110,  'max': 980},
    'givenchy':        {'avg': 210,  'min': 80,   'max': 680},
    'celine':          {'avg': 260,  'min': 95,   'max': 880},
    'moncler':         {'avg': 460,  'min': 180,  'max': 1400},
    'canada goose':    {'avg': 360,  'min': 150,  'max': 980},
    'stone island':    {'avg': 220,  'min': 90,   'max': 680},
    "arc'teryx":       {'avg': 295,  'min': 120,  'max': 780},
    'arcteryx':        {'avg': 295,  'min': 120,  'max': 780},
    'cp company':      {'avg': 185,  'min': 75,   'max': 520},
    'fear of god':     {'avg': 220,  'min': 85,   'max': 680},
    'jordan':          {'avg': 160,  'min': 65,   'max': 580},
    'yeezy':           {'avg': 240,  'min': 95,   'max': 680},
    'dunk':            {'avg': 165,  'min': 70,   'max': 480},
    'supreme':         {'avg': 140,  'min': 55,   'max': 420},
    'bape':            {'avg': 160,  'min': 65,   'max': 480},
    'palace':          {'avg': 120,  'min': 50,   'max': 340},
    'nike':            {'avg': 72,   'min': 35,   'max': 180},
    'adidas':          {'avg': 48,   'min': 22,   'max': 120},
    'new balance':     {'avg': 88,   'min': 45,   'max': 200},
    'north face':      {'avg': 98,   'min': 50,   'max': 240},
    'carhartt':        {'avg': 62,   'min': 30,   'max': 150},
    'ralph lauren':    {'avg': 48,   'min': 20,   'max': 110},
    'default':         {'avg': 25,   'min': 8,    'max': 60},
}

def estimate_sell_price(title: str, brand: str) -> float:
    s = (title + ' ' + brand).lower()
    for key, v in MARKET.items():
        if key in s:
            spread = (v['max'] - v['min']) * 0.25
            p = v['avg'] + random.uniform(-spread/2, spread/2)
            return round(max(v['min'], min(v['max'], p)), 2)
    return round(MARKET['default']['avg'] + random.uniform(-5, 10), 2)

# ── GEWINNBERECHNUNG ──────────────────────────────────────────
def calc_profit(buy: float, sell: float, platform: str = 'vinted') -> dict:
    if platform == 'vinted':
        total_buy = buy * 1.05 + 0.70
    else:
        total_buy = buy
    ebay_fee = sell * 0.12
    profit   = sell - total_buy - 4.99 - ebay_fee
    margin   = (profit / total_buy * 100) if total_buy > 0 else 0
    return {
        'profit':    round(profit, 2),
        'margin':    round(margin, 1),
        'total_buy': round(total_buy, 2),
    }

# ── INTELLIGENCE SYSTEM ───────────────────────────────────────
DEMAND_VERY_HIGH = [
    'hermès','hermes','chanel','chrome hearts','louis vuitton',
    'dior','balenciaga','rick owens','maison margiela','bottega veneta',
    'jordan','yeezy','dunk','off-white','travis scott',
]
DEMAND_HIGH = [
    'moncler','canada goose','stone island','prada','gucci',
    "arc'teryx",'arcteryx','fear of god','cp company',
    'saint laurent','celine','givenchy','supreme','bape','palace',
]
DEMAND_MEDIUM = [
    'nike','adidas','new balance','north face','carhartt',
    'ralph lauren','lacoste','napapijri','salomon',
]
FAKE_RISK_BRANDS = [
    'supreme','stone island','moncler','jordan','yeezy','off-white',
    'bape','gucci','prada','louis vuitton','balenciaga',
    'chrome hearts',"arc'teryx",'canada goose','dior','chanel',
]

def get_demand(title: str, brand: str) -> str:
    s = (title + ' ' + brand).lower()
    for b in DEMAND_VERY_HIGH:
        if b in s: return 'VERY HIGH'
    for b in DEMAND_HIGH:
        if b in s: return 'HIGH'
    for b in DEMAND_MEDIUM:
        if b in s: return 'MEDIUM'
    return 'LOW'

def get_fake_risk(brand: str, buy: float, sell: float,
                  seller_score: int, photos: int) -> str:
    s    = brand.lower()
    risk = 0
    if any(b in s for b in FAKE_RISK_BRANDS):
        ratio = buy / sell if sell > 0 else 1
        if ratio < 0.20: risk += 3
        elif ratio < 0.30: risk += 1
    if seller_score < 50: risk += 2
    elif seller_score < 65: risk += 1
    if photos == 0: risk += 2
    elif photos < 3: risk += 1
    if risk >= 4: return 'HIGH'
    if risk >= 2: return 'MEDIUM'
    return 'LOW'

def get_hot_deal(profit: float, margin: float,
                 demand: str, fake_risk: str, brand: str) -> str:
    if fake_risk == 'HIGH': return 'NORMAL'
    b      = brand.lower()
    d_high = demand in ('VERY HIGH', 'HIGH')
    is_lux = any(x in b for x in DEMAND_VERY_HIGH + DEMAND_HIGH[:8])
    if profit >= 120 and d_high and fake_risk == 'LOW': return 'ULTRA DEAL'
    if profit >= 80  and d_high and is_lux:             return 'ULTRA DEAL'
    if profit >= 50  and d_high:                        return 'FAST FLIP'
    if is_lux        and profit >= 30:                  return 'RARE FIND'
    if profit >= 30  and margin >= 50:                  return 'SMART BUY'
    return 'NORMAL'

def get_decision(profit: float, demand: str,
                 fake_risk: str, hot_deal: str) -> str:
    if fake_risk == 'HIGH' or profit < 30: return 'SKIP'
    if hot_deal == 'ULTRA DEAL' and fake_risk == 'LOW':  return 'BUY NOW'
    if hot_deal == 'FAST FLIP'  and fake_risk == 'LOW':  return 'BUY NOW'
    if hot_deal in ('RARE FIND', 'SMART BUY'):           return 'CHECK FIRST'
    if demand == 'VERY HIGH' and profit >= 50:           return 'BUY NOW'
    if demand == 'HIGH'      and profit >= 40:           return 'CHECK FIRST'
    return 'SKIP'

def normalize_item(raw: dict, platform: str) -> dict:
    title  = (raw.get('title') or 'Unbekannt').strip()
    brand  = (raw.get('brand') or '').strip()
    buy    = round(float(raw.get('price', 0) or 0), 2)
    sell   = raw.get('sell') or estimate_sell_price(title, brand)
    c      = calc_profit(buy, sell, platform)
    photos = raw.get('photos_count', 0)  # 0 = kein Foto → sofort HIGH RISK
    score  = raw.get('seller_score', 70)
    demand    = get_demand(title, brand)
    fake_risk = get_fake_risk(brand, buy, sell, score, photos)
    hot_deal  = get_hot_deal(c['profit'], c['margin'], demand, fake_risk, brand)
    decision  = get_decision(c['profit'], demand, fake_risk, hot_deal)
    return {
        'id':            str(raw.get('id', '')),
        'title':         title,
        'brand':         brand or '-',
        'condition':     raw.get('condition', '-') or '-',
        'size':          raw.get('size', '-') or '-',
        'buy':           buy,
        'sell':          round(sell, 2),
        'profit':        c['profit'],
        'margin':        c['margin'],
        'total_buy':     c['total_buy'],
        'ageSec':        raw.get('age_sec', 600),
        'image':         raw.get('image', ''),
        'images':        raw.get('images', []),
        'url':           raw.get('url', ''),
        'platform':      platform,
        'seller_score':  score,
        'demand_score':  demand,
        'fake_risk':     fake_risk,
        'hot_deal_type': hot_deal,
        'decision':      decision,
    }

# ── VINTED SESSION SYSTEM ────────────────────────────────────
_vinted_session = {'cookie': '', 'expiry': 0}
_vinted_lock    = threading.Lock()
_vinted_brand_cache = {}

# Session Tracking — sichtbar im Health-Endpoint
_session_state = {
    'ok':           False,
    'fails':        0,       # aufeinanderfolgende Fehler
    'total_ok':     0,       # erfolgreiche Requests heute
    'last_ok':      0,       # Timestamp letzter Erfolg
    'last_fail':    0,       # Timestamp letzter Fehler
    'reconnecting': False,
}

VINTED_HEADERS = {
    'User-Agent':       'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language':  'de-DE,de;q=0.9',
    'Accept':           'application/json, text/plain, */*',
    'Referer':          'https://www.vinted.de/',
    'X-Requested-With': 'XMLHttpRequest',
}

def _vinted_build_session() -> str:
    """
    Baut eine neue Vinted Session auf.
    Versucht bis zu 3x mit steigendem Timeout.
    Gibt Cookie-String zurück oder '' bei Fehler.
    """
    RETRIES = 3
    BACKOFF  = [2, 6, 12]

    for attempt in range(RETRIES):
        try:
            timeout = 10 + attempt * 4
            if _CFFI:
                s = cffi_requests.Session(impersonate='chrome124')
                r = s.get('https://www.vinted.de/', timeout=timeout)
            else:
                r = std_requests.get(
                    'https://www.vinted.de/',
                    headers=VINTED_HEADERS,
                    timeout=timeout,
                    allow_redirects=True
                )

            cookie = '; '.join(f"{k}={v}" for k, v in r.cookies.items())
            if not cookie:
                raise ValueError("Kein Cookie erhalten")

            with _vinted_lock:
                _vinted_session['cookie'] = cookie
                _vinted_session['expiry'] = time.time() + 18 * 60  # 18 Min
                _session_state['ok']       = True
                _session_state['fails']    = 0
                _session_state['last_ok']  = time.time()
                _session_state['total_ok'] += 1

            print(f"  ✓ Session OK ({len(cookie)} chars | cffi={_CFFI})")
            return cookie

        except Exception as e:
            wait = BACKOFF[attempt] if attempt < len(BACKOFF) else 15
            if attempt < RETRIES - 1:
                print(f"  ~ Session Versuch {attempt+1} fehlgeschlagen ({e}) → retry in {wait}s")
                time.sleep(wait)
            else:
                print(f"  ✗ Session fehlgeschlagen nach {RETRIES} Versuchen: {e}")
                with _vinted_lock:
                    _session_state['ok']        = False
                    _session_state['fails']     += 1
                    _session_state['last_fail']  = time.time()

    return ''

def _vinted_session_get() -> str:
    """
    Gibt aktive Session zurück.
    Baut neue Session wenn abgelaufen oder leer.
    Thread-safe.
    """
    with _vinted_lock:
        if (_vinted_session['cookie'] and
                time.time() < _vinted_session['expiry']):
            return _vinted_session['cookie']

    # Session abgelaufen — neu aufbauen
    return _vinted_build_session()

def _vinted_invalidate():
    """Session invalidieren — wird bei 401/403 aufgerufen."""
    with _vinted_lock:
        _vinted_session['cookie'] = ''
        _vinted_session['expiry'] = 0
        _session_state['ok']      = False
    print("  ~ Session invalidiert → wird neu aufgebaut")

def _session_keepalive():
    """
    Background-Thread: Refresht Session alle 15 Minuten proaktiv.
    Verhindert dass Session mitten im Scan stirbt.
    """
    while True:
        time.sleep(15 * 60)  # 15 Minuten warten
        with _vinted_lock:
            remaining = _vinted_session['expiry'] - time.time()

        if remaining < 5 * 60:  # Unter 5 Minuten Restzeit → jetzt refreshen
            print("  → Session läuft bald ab — proaktiver Refresh")
            _vinted_build_session()

# Keepalive-Thread beim Import starten
threading.Thread(target=_session_keepalive, daemon=True).start()

def _vinted_brand_id(query: str, cookie: str):
    q = query.strip().lower()
    if q in _vinted_brand_cache:
        return _vinted_brand_cache[q]
    try:
        r = std_requests.get(
            'https://www.vinted.de/api/v2/brands',
            params={'search': query, 'per_page': 5},
            headers={**VINTED_HEADERS, 'Cookie': cookie},
            timeout=5
        )
        if r.status_code == 200:
            for b in r.json().get('brands', []):
                if b.get('title', '').lower() == q:
                    bid = b['id']
                    _vinted_brand_cache[q] = bid
                    print(f"  ✓ Brand '{query}' → ID {bid}")
                    return bid
            for b in r.json().get('brands', []):
                t = b.get('title', '').lower()
                if q in t or t in q:
                    bid = b['id']
                    _vinted_brand_cache[q] = bid
                    return bid
    except Exception:
        pass
    _vinted_brand_cache[q] = None
    return None

def fetch_vinted(query: str, max_price: int = 500) -> list:
    cookie = _vinted_session_get()
    if not cookie:
        return []
    brand_id = _vinted_brand_id(query, cookie)
    
    # KRITISCH: Wenn Brand-ID gefunden → search_text LEER lassen
    # Genau so macht es Vinted selbst auf der Website
    # Beide Parameter gleichzeitig verursachen Konflikte und falsche Ergebnisse
    if brand_id:
        params = [
            ('search_text', ''),      # Leer wenn Brand-ID bekannt
            ('brand_ids[]', brand_id),
            ('price_to', max_price),
            ('order', 'newest_first'),
            ('per_page', 96),         # Max 96 für mehr Treffer
            ('page', 1),
            ('currency', 'EUR'),
        ]
        print(f"  ✓ Exakte Brand-Suche: '{query}' → brand_ids[]={brand_id}")
    else:
        # Kein Brand-ID → Text-Suche
        params = [
            ('search_text', query),
            ('price_to', max_price),
            ('order', 'newest_first'),
            ('per_page', 96),
            ('page', 1),
            ('currency', 'EUR'),
        ]
        print(f"  ~ Text-Suche: '{query}' (kein Brand-ID gefunden)")
    headers = {**VINTED_HEADERS, 'Cookie': cookie}
    try:
        if _CFFI:
            s = cffi_requests.Session(impersonate='chrome124')
            r = s.get('https://www.vinted.de/api/v2/catalog/items',
                       params=params, headers=headers, timeout=12)
        else:
            r = std_requests.get('https://www.vinted.de/api/v2/catalog/items',
                                  params=params, headers=headers, timeout=12)
        if r.status_code in (401, 403):
            print(f"  ~ Vinted {r.status_code} → Session neu aufbauen")
            _vinted_invalidate()
            new_cookie = _vinted_build_session()
            if not new_cookie:
                return []
            # Einmal retry mit neuer Session
            headers = {**VINTED_HEADERS, 'Cookie': new_cookie}
            if _CFFI:
                s2 = cffi_requests.Session(impersonate='chrome124')
                r  = s2.get('https://www.vinted.de/api/v2/catalog/items',
                             params=params, headers=headers, timeout=12)
            else:
                r = std_requests.get('https://www.vinted.de/api/v2/catalog/items',
                                      params=params, headers=headers, timeout=12)
            if r.status_code not in (200, 201):
                print(f"  ✗ Retry nach Reconnect fehlgeschlagen: {r.status_code}")
                return []
        r.raise_for_status()
        items = r.json().get('items', [])
        result = []
        for item in items:
            photo  = item.get('photo') or {}
            thumbs = photo.get('thumbnails') or []
            img    = (photo.get('url') or
                      next((t.get('url','') for t in thumbs
                            if t.get('type') == 'thumb310x430'), '') or
                      (thumbs[0].get('url','') if thumbs else ''))
            all_photos = []
            for p in (item.get('photos') or []):
                u = p.get('url', '')
                if u and u not in all_photos:
                    all_photos.append(u)
            if img and img not in all_photos:
                all_photos.insert(0, img)
            ts    = photo.get('created_at_ts') or item.get('created_at_ts') or 0
            age   = max(0, int(time.time()) - int(ts)) if ts else 600
            user  = item.get('user') or {}
            pos   = user.get('positive_feedback_count', 0) or 0
            tot   = max(user.get('feedback_count', 1) or 1, 1)
            score = min(99, max(40, round(pos / tot * 70 + 30)))
            price_raw = item.get('price', 0)
            if isinstance(price_raw, dict):
                buy = round(float(price_raw.get('amount', 0) or 0), 2)
            else:
                buy = round(float(price_raw or 0), 2)
            raw = {
                'id':           str(item.get('id', '')),
                'title':        item.get('title', 'Unbekannt'),
                'brand':        item.get('brand_title', '') or '',
                'condition':    item.get('status', '-') or '-',
                'size':         item.get('size_title', '-') or '-',
                'price':        buy,
                'image':        img,
                'images':       all_photos,
                'url':          f"https://www.vinted.de/items/{item.get('id','')}",
                'age_sec':      age,
                'seller_score': score,
                'photos_count': len(all_photos),
            }
            n = normalize_item(raw, 'vinted')
            # Brand-Filter
            q = query.strip().lower()
            brand_l = n['brand'].lower()
            title_l = n['title'].lower()
            if brand_id or (q in brand_l or (not brand_l or brand_l == '-') and q in title_l):
                result.append(n)
        print(f"  ✓ Vinted: {len(result)} Artikel für '{query}'")
        return result
    except Exception as e:
        print(f"  ✗ Vinted: {e}")
        return []

# ── EBAY ──────────────────────────────────────────────────────
EBAY_APP_ID = os.environ.get('EBAY_APP_ID', '')

def fetch_ebay_sold_price(query: str) -> float:
    if not EBAY_APP_ID:
        return 0
    try:
        r = std_requests.get(
            'https://svcs.ebay.com/services/search/FindingService/v1',
            params={
                'OPERATION-NAME': 'findCompletedItems',
                'SERVICE-VERSION': '1.0.3',
                'SECURITY-APPNAME': EBAY_APP_ID,
                'RESPONSE-DATA-FORMAT': 'JSON',
                'GLOBAL-ID': 'EBAY-DE',
                'keywords': query[:80],
                'itemFilter(0).name': 'SoldItemsOnly',
                'itemFilter(0).value': 'true',
                'sortOrder': 'EndTimeSoonest',
                'paginationInput.entriesPerPage': '10',
            },
            timeout=6
        )
        items = (r.json()
                   .get('findCompletedItemsResponse', [{}])[0]
                   .get('searchResult', [{}])[0]
                   .get('item', []))
        prices = []
        for it in items:
            try:
                p = it['sellingStatus'][0]['currentPrice'][0]
                if p.get('@currencyId') == 'EUR':
                    prices.append(float(p['__value__']))
            except Exception:
                pass
        if prices:
            avg = round(sum(prices) / len(prices), 2)
            print(f"  ✓ eBay Verkaufspreis '{query}': {avg}€")
            return avg
    except Exception as e:
        print(f"  ✗ eBay Sold: {e}")
    return 0

def fetch_ebay_listings(query: str, max_price: int = 500) -> list:
    if not EBAY_APP_ID:
        return []
    try:
        r = std_requests.get(
            'https://svcs.ebay.com/services/search/FindingService/v1',
            params={
                'OPERATION-NAME': 'findItemsByKeywords',
                'SERVICE-VERSION': '1.0.3',
                'SECURITY-APPNAME': EBAY_APP_ID,
                'RESPONSE-DATA-FORMAT': 'JSON',
                'GLOBAL-ID': 'EBAY-DE',
                'keywords': query[:80],
                'itemFilter(0).name': 'MaxPrice',
                'itemFilter(0).value': str(max_price),
                'itemFilter(0).paramName': 'Currency',
                'itemFilter(0).paramValue': 'EUR',
                'sortOrder': 'StartTimeNewest',
                'paginationInput.entriesPerPage': '48',
            },
            timeout=8
        )
        items = (r.json()
                   .get('findItemsByKeywordsResponse', [{}])[0]
                   .get('searchResult', [{}])[0]
                   .get('item', []))
        result = []
        for it in items:
            try:
                title   = it.get('title', [''])[0]
                price   = float(it.get('sellingStatus',[{}])[0]
                                   .get('currentPrice',[{}])[0]
                                   .get('__value__', 0))
                url     = it.get('viewItemURL', [''])[0]
                img     = it.get('galleryURL', [''])[0]
                item_id = it.get('itemId', [''])[0]
                cond    = it.get('condition',[{}])[0].get('conditionDisplayName',[''])[0]
                raw = {
                    'id': f'ebay_{item_id}', 'title': title,
                    'brand': query, 'condition': cond, 'size': '-',
                    'price': price, 'image': img,
                    'images': [img] if img else [],
                    'url': url, 'age_sec': 600,
                    'seller_score': 75, 'photos_count': 1 if img else 0,
                }
                result.append(normalize_item(raw, 'ebay'))
            except Exception:
                continue
        print(f"  ✓ eBay Listings: {len(result)} für '{query}'")
        return result
    except Exception as e:
        print(f"  ✗ eBay Listings: {e}")
        return []

# ── KLEINANZEIGEN ─────────────────────────────────────────────
def fetch_kleinanzeigen(query: str, max_price: int = 500) -> list:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9',
        }
        if _CFFI:
            s = cffi_requests.Session(impersonate='chrome124')
            r = s.get('https://www.kleinanzeigen.de/s-suchanfrage.html',
                       params={'keywords': query, 'maxPrice': max_price},
                       headers=headers, timeout=12)
        else:
            r = std_requests.get('https://www.kleinanzeigen.de/s-suchanfrage.html',
                                   params={'keywords': query, 'maxPrice': max_price},
                                   headers=headers, timeout=12)
        if r.status_code != 200:
            return []
        ad_ids  = re.findall(r'data-adid="(\d+)"', r.text)
        prices  = re.findall(r'class="[^"]*price[^"]*"[^>]*>([^<]+)<', r.text)
        titles  = re.findall(r'class="[^"]*ellipsis[^"]*"[^>]*>([^<]+)<', r.text)
        imgs    = re.findall(r'data-imgsrc="([^"]+)"', r.text)
        result  = []
        for i, ad_id in enumerate(ad_ids[:48]):
            try:
                title = titles[i].strip() if i < len(titles) else query
                ps    = (prices[i].replace('€','').replace('.','')
                                  .replace(',','.').strip() if i < len(prices) else '0')
                price = float(re.sub(r'[^\d.]', '', ps)) if ps else 0.0
                if price <= 0 or price > max_price:
                    continue
                img = imgs[i] if i < len(imgs) else ''
                raw = {
                    'id': f'kaz_{ad_id}', 'title': title,
                    'brand': query, 'condition': '-', 'size': '-',
                    'price': price, 'image': img,
                    'images': [img] if img else [],
                    'url': f'https://www.kleinanzeigen.de/s-anzeige/{ad_id}',
                    'age_sec': 600, 'seller_score': 65, 'photos_count': 1 if img else 0,
                }
                result.append(normalize_item(raw, 'kleinanzeigen'))
            except Exception:
                continue
        print(f"  ✓ Kleinanzeigen: {len(result)} für '{query}'")
        return result
    except Exception as e:
        print(f"  ✗ Kleinanzeigen: {e}")
        return []

# ── MULTI-PLATFORM SEARCH ─────────────────────────────────────
def search_all(query: str, max_price: int = 500,
               platforms: list = None) -> list:
    if not platforms:
        platforms = ['vinted', 'ebay', 'kleinanzeigen']
    results = []
    lock    = threading.Lock()

    def _fetch(p):
        try:
            if p == 'vinted':
                items = fetch_vinted(query, max_price)
            elif p == 'ebay':
                items = fetch_ebay_listings(query, max_price)
            elif p == 'kleinanzeigen':
                items = fetch_kleinanzeigen(query, max_price)
            else:
                items = []
            with lock:
                results.extend(items)
        except Exception as e:
            print(f"  ✗ {p}: {e}")

    threads = [threading.Thread(target=_fetch, args=(p,), daemon=True) for p in platforms]
    for t in threads: t.start()
    for t in threads: t.join(timeout=15)

    # Deduplizieren + sortieren nach Profit
    seen = set()
    unique = []
    for item in results:
        if item['id'] not in seen:
            seen.add(item['id'])
            unique.append(item)
    unique.sort(key=lambda x: x['profit'], reverse=True)
    print(f"  ✓ Total: {len(unique)} Artikel von {platforms}")
    return unique

# ── ENDPOINTS ─────────────────────────────────────────────────
_app_start = time.time()

@app.route('/api/health')
def health():
    return jsonify({
        'status':          'ok',
        'version':         '4.2',
        'cffi':            _CFFI,
        'ebay':            bool(EBAY_APP_ID),
        'vinted':          bool(_vinted_session['cookie']),
        'session_ok':      _session_state['ok'],
        'session_fails':   _session_state['fails'],
        'session_last_ok': round(_session_state['last_ok']),
        'uptime_sec':      round(time.time() - _app_start),
        'time':            int(time.time()),
    })

@app.route('/api/search')
def search():
    query     = request.args.get('query', '').strip()
    max_price = int(request.args.get('maxPrice', 500))
    plats     = request.args.get('platforms', 'vinted').split(',')
    plats     = [p.strip() for p in plats if p.strip()]
    if not query:
        return jsonify({'success': False, 'error': 'Kein Suchbegriff', 'items': []})
    t0    = time.time()
    items = search_all(query, max_price, plats)
    ms    = round((time.time() - t0) * 1000)
    return jsonify({'success': True, 'items': items, 'total': len(items),
                    'query': query, 'ms': ms})

@app.route('/api/ebay-sold')
def ebay_sold():
    query = request.args.get('query', '')
    price = fetch_ebay_sold_price(query)
    return jsonify({'success': True, 'soldPrice': price})

@app.route('/api/marketprice')
def marketprice():
    title = request.args.get('title', '')
    brand = request.args.get('brand', '')
    return jsonify({'success': True, 'marketPrice': estimate_sell_price(title, brand)})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:p>')
def static_files(p):
    return send_from_directory('.', p)

# ── START ─────────────────────────────────────────────────────
if __name__ == '__main__':
    print('\n' + '═'*52)
    print('  FLIPP v4.2 – Luxury Arbitrage Scanner')
    print(f'  http://localhost:{PORT}')
    print('═'*52)
    print(f'  curl_cffi : {"✓" if _CFFI else "✗  pip install curl_cffi"}')
    print(f'  eBay API  : {"✓" if EBAY_APP_ID else "✗  EBAY_APP_ID nicht gesetzt"}')
    print('  Vinted    : Session aufbauen (bis 3 Versuche)…')
    print('═'*52 + '\n')
    ok = _vinted_build_session()
    print('  ✓ Bereit — Vinted Session aktiv\n' if ok else '  ~ Session Fehler — Keepalive versucht alle 15 Min\n')
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
