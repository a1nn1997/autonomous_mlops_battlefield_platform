import asyncio
import time
import numpy as np
import httpx
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table

console = Console()

SAMPLE_PAYLOAD = {
    "items": [
        {
            "store_id": "STORE_01",
            "item_id": "ITEM_001",
            "dept_id": "FOODS_1",
            "sell_price": 4.50,
            "is_promo": 1,
            "is_weekend": 0,
            "day_of_week": 3,
            "month": 6,
            "lag_1": 28.0,
            "lag_7": 26.0,
            "lag_14": 27.0,
            "lag_28": 25.0,
            "rolling_mean_7": 27.2,
            "rolling_std_7": 1.8,
            "rolling_mean_14": 26.8,
            "rolling_std_14": 2.1,
            "rolling_mean_28": 26.0,
            "rolling_std_28": 2.3,
            "price_ratio_28": 0.95,
            "price_diff_7": -0.25,
            "dow_sin": 0.43,
            "dow_cos": -0.90,
            "month_sin": 0.12,
            "month_cos": 0.99
        }
    ]
}

async def send_request(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        resp = await client.post(url, json=SAMPLE_PAYLOAD, timeout=5.0)
        lat = (time.perf_counter() - start) * 1000.0
        return {"status": resp.status_code, "latency_ms": lat, "ok": resp.status_code == 200}
    except Exception as e:
        lat = (time.perf_counter() - start) * 1000.0
        return {"status": 500, "latency_ms": lat, "ok": False, "error": str(e)}

async def run_load_test(
    url: str = "http://127.0.0.1:8000/predict",
    total_requests: int = 250,
    concurrency: int = 20
):
    console.rule(f"[bold cyan]HA Serving Load Test: {total_requests} requests at concurrency={concurrency}[/bold cyan]")
    
    limits = httpx.Limits(max_connections=concurrency + 5, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(limits=limits) as client:
        # Warmup request
        try:
            await client.get(url.replace("/predict", "/health"))
        except Exception:
            pass

        semaphore = asyncio.Semaphore(concurrency)

        async def worker():
            async with semaphore:
                return await send_request(client, url)

        wall_start = time.perf_counter()
        tasks = [asyncio.create_task(worker()) for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)
        wall_time = time.perf_counter() - wall_start

    # Metrics computation
    latencies = [r["latency_ms"] for r in results if r["ok"]]
    success_count = sum(1 for r in results if r["ok"])
    error_count = len(results) - success_count
    rps = len(results) / wall_time if wall_time > 0 else 0.0

    if not latencies:
        console.print(f"[red]All {len(results)} requests failed. Is the server running on {url}?[/red]")
        return

    p50 = np.percentile(latencies, 50)
    p90 = np.percentile(latencies, 90)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    table = Table(title="Load Test Summary: Latency & Throughput")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total Requests", str(total_requests))
    table.add_row("Concurrent Workers", str(concurrency))
    table.add_row("Successful Responses", f"[green]{success_count} ({success_count/total_requests:.1%})[/green]")
    table.add_row("Failed Responses", f"[red]{error_count}[/red]" if error_count else "0")
    table.add_row("Total Wall Time", f"{wall_time:.2f} s")
    table.add_row("Throughput (RPS)", f"[bold green]{rps:.1f} req/sec[/bold green]")
    table.add_row("Latency p50 (Median)", f"[bold green]{p50:.2f} ms[/bold green]")
    table.add_row("Latency p90", f"{p90:.2f} ms")
    table.add_row("Latency p95", f"[bold yellow]{p95:.2f} ms[/bold yellow]")
    table.add_row("Latency p99", f"{p99:.2f} ms")
    table.add_row("Min Latency", f"{min(latencies):.2f} ms")
    table.add_row("Max Latency", f"{max(latencies):.2f} ms")

    console.print(table)

if __name__ == "__main__":
    asyncio.run(run_load_test())
