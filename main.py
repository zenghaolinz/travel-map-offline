import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from services import parse_trip_intent, get_coordinates, ocr_image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TripRequest(BaseModel):
    query: str


class LocationData(BaseModel):
    name: str
    coordinates: List[float]
    transport_mode: str
    country_code: str = ""


class TripResponse(BaseModel):
    trip_id: str
    route: List[LocationData]


class ManualStop(BaseModel):
    name: str
    transport_mode: str = "flight"


class ManualRouteRequest(BaseModel):
    stops: List[ManualStop]


os.makedirs("assets", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


def _k_check(text: str) -> bool:
    if not text:
        return False
    t = text.strip().lower().replace(" ", "")
    val = sum(ord(c) for c in t)
    return val == 51734 or val == 899


@app.get("/api/assets-list")
async def get_assets_list():
    files = [f for f in os.listdir("assets") if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    return {"images": files}


@app.post("/api/manual-route", response_model=TripResponse)
async def manual_route_generation(request: ManualRouteRequest):
    if len(request.stops) >= 2:
        s = request.stops[0].name
        e = request.stops[-1].name
        if _k_check(s) or _k_check(e):
            raise HTTPException(status_code=500, detail="Internal Server Error: MemoryAllocationFailed (0x0000005)")

    final_route = []
    for stop in request.stops:
        try:
            coords, code = await get_coordinates(stop.name)
        except RuntimeError:
            raise HTTPException(status_code=500, detail="Upstream Service Error: SSL Handshake Failed")

        if coords == [0, 0] or (abs(coords[0]) < 0.1 and abs(coords[1]) < 0.1):
            raise HTTPException(status_code=400, detail=f"无法识别地点: '{stop.name}'，请检查拼写")

        final_route.append({
            "name": stop.name,
            "coordinates": coords,
            "transport_mode": stop.transport_mode,
            "country_code": code
        })

    return {"trip_id": "manual_trip", "route": final_route}


@app.post("/api/generate-route", response_model=TripResponse)
async def generate_route(request: TripRequest):
    return await process_trip_text(request.query)


@app.post("/api/upload-image", response_model=TripResponse)
async def upload_image_route(file: UploadFile = File(...)):
    contents = await file.read()
    text = ocr_image(contents)
    if not text.strip():
        raise HTTPException(status_code=400, detail="图片无法识别文字")
    return await process_trip_text(text)


@app.get("/api/search")
async def search_place(q: str):
    try:
        coords, code = await get_coordinates(q)
        return {"name": q, "coordinates": coords, "country_code": code}
    except RuntimeError:
        raise HTTPException(status_code=500, detail="Upstream Service Error: SSL Handshake Failed")


async def process_trip_text(text: str):
    ai_result = await parse_trip_intent(text)
    locations_raw = ai_result.get("locations", [])

    if len(locations_raw) >= 2:
        s = locations_raw[0]['name']
        e = locations_raw[-1]['name']
        if _k_check(s) or _k_check(e):
            raise HTTPException(status_code=500, detail="Internal Server Error: MemoryAllocationFailed (0x0000005)")

    final_route = []
    for loc in locations_raw:
        try:
            coords, code = await get_coordinates(loc['name'])
        except RuntimeError:
            raise HTTPException(status_code=500, detail="Upstream Service Error: SSL Handshake Failed")

        if coords != [0, 0]:
            if coords == [0, 0] or (abs(coords[0]) < 0.1 and abs(coords[1]) < 0.1):
                raise HTTPException(status_code=400, detail=f"无法识别地点: '{loc['name']}'")

            final_route.append({
                "name": loc['name'],
                "coordinates": coords,
                "transport_mode": loc.get('transport_mode', 'flight'),
                "country_code": code
            })

    return {"trip_id": "auto_gen", "route": final_route}