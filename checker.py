import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import asyncio
from typing import List, Dict, Any

USER_AGENTS = [
    # A few common UAs to avoid naive blocks
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/126.0",
]

IP_ONLY_RE = re.compile(r"^\s*(\d{1,3}(?:\.\d{1,3}){3})\s*$")
IP_PORT_RE = re.compile(
    r"^\s*(?:(?P<user>[^:@\s]+):(?P<pass>[^@\s]+)@)?(?P<ip>\d{1,3}(?:\.\d{1,3}){3})(?::(?P<port>\d{1,5}))?\s*$"
)

def normalize_targets(raw: List[str], try_ports: List[int]) -> List[Dict[str, str]]:
    """
    Takes raw lines (IP / IP:PORT / user:pass@IP:PORT) and returns a list of proxy strings to try.
    If only IP is present, expand to IP with common ports.
    """
    targets = []
    for line in raw:
        if not line or not str(line).strip():
            continue
        m = IP_PORT_RE.match(line.strip())
        if not m:
            # skip invalid rows
            continue
        user = m.group("user")
        pw = m.group("pass")
        ip = m.group("ip")
        port = m.group("port")

        creds = f"{user}:{pw}@" if user and pw else ""
        if port:
            proxy = f"http://{creds}{ip}:{port}"
            targets.append({"input": line.strip(), "proxy": proxy})
        else:
            for p in try_ports:
                proxy = f"http://{creds}{ip}:{p}"
                targets.append({"input": line.strip(), "proxy": proxy})
    # De-duplicate by proxy url but preserve input reference
    seen = set()
    unique = []
    for t in targets:
        if t["proxy"] not in seen:
            unique.append(t)
            seen.add(t["proxy"])
    return unique

def try_request(target_url: str, proxy_url: str, timeout: float) -> Dict[str, Any]:
    """
    Attempt to reach target_url through proxy_url.
    Strategy:
      1) HEAD (fast) allow redirects
      2) If HEAD fails, GET (fallback)
    Checks:
      - any 2xx/3xx considered reachable (status 'real')
      - records final_url and timing
    """
    headers = {"User-Agent": USER_AGENTS[0]}
    proxies = {"http": proxy_url, "https": proxy_url}
    start = time.perf_counter()
    try:
        # Step 1: HEAD
        r = requests.head(
            target_url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
            allow_redirects=True,
            verify=False,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        if 200 <= r.status_code < 400:
            return {
                "normalized_proxy": proxy_url,
                "status": "real",
                "http_status": r.status_code,
                "elapsed_ms": elapsed,
                "final_url": r.url,
                "error": "",
            }
    except Exception as e:
        head_error = str(e)
    else:
        head_error = ""

    # Step 2: GET fallback if HEAD not conclusive
    start2 = time.perf_counter()
    try:
        r = requests.get(
            target_url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
            allow_redirects=True,
            verify=False,
            stream=False,
        )
        elapsed2 = int((time.perf_counter() - start2) * 1000)
        if 200 <= r.status_code < 400:
            return {
                "normalized_proxy": proxy_url,
                "status": "real",
                "http_status": r.status_code,
                "elapsed_ms": elapsed2,
                "final_url": r.url,
                "error": "",
            }
        else:
            return {
                "normalized_proxy": proxy_url,
                "status": "fake",
                "http_status": r.status_code,
                "elapsed_ms": elapsed2,
                "final_url": r.url,
                "error": "",
            }
    except Exception as e:
        return {
            "normalized_proxy": proxy_url,
            "status": "fake",
            "http_status": None,
            "elapsed_ms": int((time.perf_counter() - start2) * 1000),
            "final_url": "",
            "error": head_error or str(e),
        }

def check_one(input_label: str, proxy_url: str, target_url: str, timeout: float) -> Dict[str, Any]:
    res = try_request(target_url, proxy_url, timeout)
    res["input"] = input_label
    return res

async def check_proxies_bulk(
    raw_ips: List[str],
    target_url: str,
    timeout: float = 6.0,
    max_workers: int = 20,
    try_ports: List[int] = None,
) -> List[Dict[str, Any]]:
    if try_ports is None:
        try_ports = [80, 8080, 3128, 8000, 8888]
    targets = normalize_targets(raw_ips, try_ports)
    results: List[Dict[str, Any]] = []
    if not targets:
        return results
    # Run parallel with threads (requests is blocking)
    loop = asyncio.get_event_loop()
    def run_pool():
        out = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [
                pool.submit(check_one, t["input"], t["proxy"], target_url, timeout)
                for t in targets
            ]
            for f in as_completed(futures):
                out.append(f.result())
        return out
    results = await loop.run_in_executor(None, run_pool)
    # Collapse multiple attempts for the same input row:
    # Mark "real" if any of its proxy attempts succeeded.
    collapsed: Dict[str, Dict[str, Any]] = {}
    for r in results:
        key = r["input"]
        if key not in collapsed:
            collapsed[key] = r
        else:
            # Prefer a real over fake
            if collapsed[key]["status"] != "real" and r["status"] == "real":
                collapsed[key] = r
            # Or keep the fastest real
            elif (
                collapsed[key]["status"] == "real" and r["status"] == "real"
                and (r.get("elapsed_ms") or 999999) < (collapsed[key].get("elapsed_ms") or 999999)
            ):
                collapsed[key] = r
    # If an input expanded to multiple proxies and all were fake, keep the first for reporting
    return list(collapsed.values()) 