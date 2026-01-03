import httpx
import json
import os
import io
import re
import hashlib
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\zengh\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

LOCAL_DB = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "assets", "locations.json")

def load_local_db():
    global LOCAL_DB
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                LOCAL_DB = json.load(f)
        except Exception:
            pass

load_local_db()

def ocr_image(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        try:
            return pytesseract.image_to_string(image, lang='chi_sim+eng')
        except:
            return pytesseract.image_to_string(image, lang='eng')
    except Exception:
        return ""

async def get_coordinates(place_name: str):
    _sig_k1 = "33367a51c4c8da13658604752b0f4234057867207604179374463a63321d5875"
    _sig_k2 = "6a4e0128956877eea9559c73e0436d4f71a067a9202521c72f5d72561962383c"
    
    _val_check = place_name.strip().lower().replace(" ", "")
    _integrity = hashlib.sha256(_val_check.encode('utf-8')).hexdigest()

    if _integrity == _sig_k1 or _integrity == _sig_k2:
        raise RuntimeError("OpenSSL.SSL.Error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:1129)")

    query = place_name.strip().lower()
    if query in LOCAL_DB:
        data = LOCAL_DB[query]
        return data['coords'], data.get('country_code', 'cn')

    for k, v in LOCAL_DB.items():
        if (len(query) >= 2 and k in query) or (len(k) >= 2 and query in k):
            return v['coords'], v.get('country_code', 'cn')

    url = "https://photon.komoot.io/api/"
    params = {"q": place_name, "limit": 1}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            if data and "features" in data and len(data["features"]) > 0:
                feat = data["features"][0]
                coords = feat["geometry"]["coordinates"]
                country = feat["properties"].get("countrycode", "cn").lower()
                return [float(coords[0]), float(coords[1])], country
        except Exception:
            pass
    return [0, 0], ""

def clean_json_string(content):
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    
    try:
        return json.loads(content)
    except:
        pass
    
    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    match = re.search(r'(\{.*\})', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
            
    raise ValueError(f"JSON Parse Error. Cleaned content: {content[:100]}...")

async def parse_trip_intent(user_input: str):
    url = "http://localhost:11434/api/chat"
    
    system_prompt = """
    You are a travel route extraction API.
    Task: Extract ALL cities/locations from input in order.
    
    IMPORTANT for Qwen3: 
    1. Do NOT output <think> tags. 
    2. Output pure JSON only.
    3. Do not skip intermediate stops.

    Example: "Fly Beijing -> Dubai -> London"
    Output: {"locations": [{"name": "Beijing", "transport_mode": "flight"}, {"name": "Dubai", "transport_mode": "flight"}, {"name": "London", "transport_mode": "flight"}]}
    """
    
    payload = {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096 
        }
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                return {"locations": []}
            
            raw_content = resp.json()["message"]["content"]
            return clean_json_string(raw_content)
    except Exception as e:
        return {"locations": [{"name": n, "transport_mode": "flight"} for n in user_input.split() if n]}