import httpx
import json
import os
import io
import re
import hashlib
from PIL import Image
import pytesseract

# Tesseract 路径
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
    query = place_name.strip().lower()
    if query in LOCAL_DB:
        data = LOCAL_DB[query]
        return data['coords'], data.get('country_code', 'cn')

    for k, v in LOCAL_DB.items():
        if (len(query) >= 2 and k in query) or (len(k) >= 2 and query in k):
            return v['coords'], v.get('country_code', 'cn')

    # 联网兜底
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
    """
    清洗函数升级：适配 Qwen3 的 <think> 标签
    """
    # 1. 移除 <think>...</think> 的思维链内容，这东西会破坏 JSON
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    
    # 2. 尝试直接解析
    try:
        return json.loads(content)
    except:
        pass
    
    # 3. 提取 ```json 代码块
    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    # 4. 暴力提取 {}
    match = re.search(r'(\{.*\})', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
            
    raise ValueError(f"JSON Parse Error. Cleaned content: {content[:100]}...")

async def parse_trip_intent(user_input: str):
    url = "http://localhost:11434/api/chat"
    
    # 针对 Qwen3 优化的 Prompt，禁止它过度思考，直接输出结果
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
    
    # ✅ 这里改成了 qwen3:8b
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
                print(f"❌ Ollama Error: {resp.text}")
                return {"locations": []}
            
            raw_content = resp.json()["message"]["content"]
            # print(f"🔍 Debug Qwen3 Raw: {raw_content}") # 调试用
            return clean_json_string(raw_content)
    except Exception as e:
        print(f"❌ Error: {e}")
        # 降级处理
        return {"locations": [{"name": n, "transport_mode": "flight"} for n in user_input.split() if n]}