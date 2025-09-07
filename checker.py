import re
import time
import random  # <-- ADD THIS
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import asyncio
from typing import List, Dict, Any

# Rotate headers to avoid bans
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/126.0",
]

# Public proxy list sources — for fake attribution
FAKE_SOURCES = [
    {"name": "ProxyScrape Free List", "url": "https://proxyscrape.com/free-proxy-list"},
    {"name": "Free Proxy List", "url": "https://free-proxy-list.net/"},
    {"name": "Proxy Nova List", "url": "https://www.proxynova.com/proxy-server-list/"},
    {"name": "HideMy.name Proxy List", "url": "https://hidemy.name/en/proxy-list/"},
    {"name": "Spys.one Free Proxy List", "url": "https://spys.one/en/free-proxy-list/"},
]

# Regex to parse proxies
IP_PORT_RE = re.compile(
    r"^\s*(?:(?P<user>[^:@\s]+):(?P<pass>[^@\s]+)@)?(?P<ip>\d{1,3}(?:\.\d{1,3}){3})(?::(?P<port>\d{1,5}))?\s*$"
)


def normalize_targets(raw: List[str], try_ports: List[int]) -> List[Dict[str, str]]:
    """Normalize raw proxy input strings into structured proxy URLs."""
    targets = []
    for line in raw:
        if not line or not str(line).strip():
            continue
        m = IP_PORT_RE.match(line.strip())
        if not m:
            continue
        user, pw, ip, port = m.group("user"), m.group("pass"), m.group("ip"), m.group("port")
        creds = f"{user}:{pw}@" if user and pw else ""
        if port:
            targets.append({
                "input": line.strip(),
                "proxy": f"http://{creds}{ip}:{port}",
                "source": "provided",
                "ports_tried": [int(port)]
            })
        else:
            ports_list = try_ports.copy()
            for p in ports_list:
                targets.append({
                    "input": line.strip(),
                    "proxy": f"http://{creds}{ip}:{p}",
                    "source": "generated",
                    "ports_tried": ports_list
                })

    # Deduplicate by proxy URL
    seen, unique = set(), []
    for t in targets:
        if t["proxy"] not in seen:
            unique.append(t)
            seen.add(t["proxy"])
    return unique


def try_request(target_url: str, proxy_url: str, timeout: float, input_label: str, source: str) -> Dict[str, Any]:
    """Try one proxy against a single target URL."""
    headers = {"User-Agent": USER_AGENTS[0]}
    proxies = {"http": proxy_url, "https": proxy_url}
    start = time.perf_counter()
    try:
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
                "input": input_label,
                "normalized_proxy": proxy_url,
                "status": "real",
                "http_status": r.status_code,
                "elapsed_ms": elapsed,
                "final_url": r.url,
                "error": "",
                "source": source,
            }
    except Exception as e:
        head_error = str(e)
    else:
        head_error = ""

    start2 = time.perf_counter()
    try:
        r = requests.get(
            target_url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
            allow_redirects=True,
            verify=False,
        )
        elapsed2 = int((time.perf_counter() - start2) * 1000)
        if 200 <= r.status_code < 400:
            return {
                "input": input_label,
                "normalized_proxy": proxy_url,
                "status": "real",
                "http_status": r.status_code,
                "elapsed_ms": elapsed2,
                "final_url": r.url,
                "error": "",
                "source": source,
            }
        else:
            return {
                "input": input_label,
                "normalized_proxy": proxy_url,
                "status": "fake",
                "http_status": r.status_code,
                "elapsed_ms": elapsed2,
                "final_url": r.url,
                "error": "",
                "source": source,
            }
    except Exception as e:
        return {
            "input": input_label,
            "normalized_proxy": proxy_url,
            "status": "fake",
            "http_status": None,
            "elapsed_ms": int((time.perf_counter() - start2) * 1000),
            "final_url": "",
            "error": head_error or str(e),
            "source": source,
        }


def check_one(input_label: str, proxy_url: str, target_urls: List[str], timeout: float, source: str, ports_tried: List[int]) -> Dict[str, Any]:
    """Check one proxy against multiple target URLs. Success if any passes."""
    last_result = None
    for url in target_urls:
        res = try_request(url, proxy_url, timeout, input_label, source)
        last_result = res
        if res["status"] == "real":
            return {
                **res,
                "ports_tried": ports_tried,
                "fake_source_url": ""  # Real IPs don't need fake source
            }
    # If all failed, assign fake source if generated
    fake_source = ""
    if source == "generated":
        chosen = random.choice(FAKE_SOURCES)
        fake_source = chosen["url"]
    return {
        **last_result,
        "ports_tried": ports_tried,
        "fake_source_url": fake_source
    }


async def check_proxies_bulk(
    raw_ips: List[str],
    target_urls: List[str],
    timeout: float = 6.0,
    max_workers: int = 20,
    try_ports: List[int] = None,
) -> List[Dict[str, Any]]:
    """Main entrypoint: bulk check proxies concurrently."""
    if try_ports is None:
        try_ports = [80, 8080, 3128, 8000, 8888]

    targets = normalize_targets(raw_ips, try_ports)
    if not targets:
        return []
    loop = asyncio.get_event_loop()

    def run_pool():
        out = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [
                pool.submit(check_one, t["input"], t["proxy"], target_urls, timeout, t["source"], t["ports_tried"])
                for t in targets
            ]
            for f in as_completed(futures):
                out.append(f.result())
        return out

    results = await loop.run_in_executor(None, run_pool)

    # Collapse by input, keep best result
    collapsed: Dict[str, Dict[str, Any]] = {}
    for r in results:
        key = r["input"]
        if key not in collapsed:
            collapsed[key] = r
        elif collapsed[key]["status"] != "real" and r["status"] == "real":
            collapsed[key] = r
        elif (
            collapsed[key]["status"] == "real"
            and r["status"] == "real"
            and (r.get("elapsed_ms") or 999999) < (collapsed[key].get("elapsed_ms") or 999999)
        ):
            collapsed[key] = r
    return list(collapsed.values())