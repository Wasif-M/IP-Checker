import csv
import io
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from checker import check_proxies_bulk

app = FastAPI(title="DOT 5 - Advanced Bulk IP Checker")

# Serve the frontend - mount at /static to avoid conflicts with API
app.mount("/static", StaticFiles(directory="public"), name="static")

TARGET_URL = "http://bathrooms-renovation.xyz/"


@app.get("/")
async def root():
    """Serve the main HTML page"""
    with open("public/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return PlainTextResponse(content, media_type="text/html")


@app.get("/style.css")
async def get_css():
    """Serve the CSS file"""
    with open("public/style.css", "r", encoding="utf-8") as f:
        content = f.read()
    return PlainTextResponse(content, media_type="text/css")


@app.get("/app.js")
async def get_js():
    """Serve the JavaScript file"""
    with open("public/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    return PlainTextResponse(content, media_type="application/javascript")


@app.post("/api/check-bulk")
async def api_check_bulk(req: Request):
    payload = await req.json()
    raw_ips = payload.get("ips", [])
    timeout = float(payload.get("timeout", 6.0))
    max_workers = int(payload.get("max_workers", 20))
    try_ports = payload.get("try_ports", [80, 8080, 3128, 8000, 8888])

    results = await check_proxies_bulk(
        raw_ips=raw_ips,
        target_url=TARGET_URL,
        timeout=timeout,
        max_workers=max_workers,
        try_ports=try_ports,
    )
    return JSONResponse(results)


@app.post("/api/export-csv")
async def api_export_csv(req: Request):
    """
    Accepts a JSON body { "results": [...] } and returns CSV.
    """
    payload = await req.json()
    rows = payload.get("results", [])
    # Build CSV
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "input",
            "normalized_proxy",
            "status",
            "http_status",
            "elapsed_ms",
            "final_url",
            "error",
        ],
        extrasaction="ignore",
    )
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    csv_bytes = output.getvalue().encode("utf-8")
    return PlainTextResponse(
        content=csv_bytes.decode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=dot5_results.csv"
        },
    ) 