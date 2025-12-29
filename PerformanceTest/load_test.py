import asyncio
import aiohttp
import time
import numpy as np
from collections import defaultdict
from tqdm import tqdm

# ================= CONFIG =================

NODE = "http://localhost:3000"
DOTNET = "http://localhost:5500"
GO = "http://localhost:8080"
DOTNET_AOT = "http://localhost:5600"


TEST_DURATION = 30      # seconds per test
WARMUP_DURATION = 5
TIMEOUT = aiohttp.ClientTimeout(total=30)

RESULTS = defaultdict(dict)

# ================= UTIL =================

async def warmup(url):
    print(f"☀️  Warming up {url}")
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        start = time.time()
        while time.time() - start < WARMUP_DURATION:
            try:
                async with session.get(url) as r:
                    await r.read()
            except:
                pass
    print("🔥  Warmup complete\n")

async def cool_down(seconds=10):
    print(f"\n❄️  Cooling down for {seconds} seconds...")
    for i in range(seconds, 0, -1):
        print(f"   Resuming in {i}s", end="\r")
        await asyncio.sleep(1)
    print("\n🔥  Ready for next round!\n")

async def run_test(label, runtime, url, concurrency):
    latencies = []
    errors = 0
    completed = 0

    semaphore = asyncio.Semaphore(concurrency)

    async def worker(session):
        nonlocal errors, completed
        async with semaphore:
            start = time.perf_counter()
            try:
                async with session.get(url) as resp:
                    await resp.read()  # IMPORTANT
                    if resp.status == 200:
                        latencies.append(time.perf_counter() - start)
                    else:
                        errors += 1
            except:
                errors += 1
            completed += 1

    print(f"[{label}] {runtime} → {concurrency} concurrent users")

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        start_time = time.time()
        with tqdm(desc=f"{label} | {runtime}", unit="req") as bar:
            while time.time() - start_time < TEST_DURATION:
                await asyncio.gather(
                    *[worker(session) for _ in range(concurrency)]
                )
                bar.update(completed - bar.n)

    return latencies, errors

def summarize(latencies, errors):
    if not latencies:
        return {
            "avg": None,
            "p95": None,
            "p99": None,
            "errors": errors,
            "count": 0
        }

    arr = np.array(latencies)
    return {
        "avg": float(arr.mean()),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "errors": errors,
        "count": len(arr)
    }

def fmt(val):
    return f"{val:.4f}" if isinstance(val, float) else "N/A"

# ================= TEST ROUNDS =================

async def baseline_test():
    print("\n--- ROUND 0: BASELINE (IO, SINGLE USER) ---")
    for name, base in [("Node.js", NODE), ("Dotnet", DOTNET), ("Go", GO), ("Dotnet AOT", DOTNET_AOT)]:
        url = f"{base}/io"
        await warmup(url)
        lat, err = await run_test("Baseline", name, url, concurrency=1)
        RESULTS["Baseline"][name] = summarize(lat, err)

async def io_test():
    print("\n--- ROUND 1: IO-BOUND (ASYNC SCALABILITY) ---")
    for name, base in [("Node.js", NODE), ("Dotnet", DOTNET), ("Go", GO), ("Dotnet AOT", DOTNET_AOT)]:
        url = f"{base}/io"
        await warmup(url)
        lat, err = await run_test("IO", name, url, concurrency=200)
        RESULTS["IO"][name] = summarize(lat, err)

async def cpu_test():
    print("\n--- ROUND 2: CPU-BOUND (PRIME CALCULATION) ---")
    for name, base in [("Node.js", NODE), ("Dotnet", DOTNET), ("Go", GO), ("Dotnet AOT", DOTNET_AOT)]:
        url = f"{base}/heavy"
        await warmup(url)
        lat, err = await run_test("CPU", name, url, concurrency=4)
        RESULTS["CPU"][name] = summarize(lat, err)

async def sustained_test():
    print("\n--- ROUND 3: SUSTAINED LOAD (TAIL LATENCY) ---")
    for name, base in [("Node.js", NODE), ("Dotnet", DOTNET), ("Go", GO), ("Dotnet AOT", DOTNET_AOT)]:
        url = f"{base}/io"
        await warmup(url)
        lat, err = await run_test("Sustained", name, url, concurrency=300)
        RESULTS["Sustained"][name] = summarize(lat, err)

# ================= HTML REPORT =================

def generate_html():
    def block(test):
        n = RESULTS[test]["Node.js"]
        d = RESULTS[test]["Dotnet"]
        g = RESULTS[test]["Go"]
        d_aot = RESULTS[test]["Dotnet AOT"]
        return f"""
        <div class="card">
            <h2>{test}</h2>
            <canvas id="{test}Chart"></canvas>
            <div class="stats">
                Avg: Node {fmt(n['avg'])}s | .NET {fmt(d['avg'])}s | Go {fmt(g['avg'])}s | .NET AOT {fmt(d_aot['avg'])}s<br/>
                P95: Node {fmt(n['p95'])}s | .NET {fmt(d['p95'])}s | Go {fmt(g['p95'])}s | .NET AOT {fmt(d_aot['p95'])}s<br/>
                P99: Node {fmt(n['p99'])}s | .NET {fmt(d['p99'])}s | Go {fmt(g['p99'])}s | .NET AOT {fmt(d_aot['p99'])}s<br/>
                Errors: Node {n['errors']} | .NET {d['errors']} | Go {g['errors']} | .NET AOT {d_aot['errors']}<br/>
                Samples: Node {n['count']} | .NET {d['count']} | Go {g['count']} | .NET AOT {d_aot['count']}
            </div>
        </div>
        """

    def chart(test):
        n = RESULTS[test]["Node.js"]["avg"] or 0
        d = RESULTS[test]["Dotnet"]["avg"] or 0
        g = RESULTS[test]["Go"]["avg"] or 0
        d_aot = RESULTS[test]["Dotnet AOT"]["avg"] or 0
        return f"""
        new Chart(document.getElementById('{test}Chart'), {{
            type: 'bar',
            data: {{
                labels: ['Node.js', '.NET', 'Go', '.NET AOT'],
                datasets: [{{
                    label: 'Avg Response (s)',
                    data: [{n}, {d}, {g}, {d_aot}],
                    backgroundColor: ['#68a063', '#512bd4', '#00ADD8', '#FF0000']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ y: {{ beginAtZero: true }} }}
            }}
        }});
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>Node.js vs .NET vs Go – Performance Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{ font-family: system-ui; background:#f4f6f8; padding:30px }}
.container {{ max-width:1200px; margin:auto; background:#fff; padding:30px; border-radius:12px }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:30px }}
.card {{ padding:20px; border:1px solid #ddd; border-radius:10px }}
.stats {{ text-align:center; color:#555; margin-top:10px }}
h1 {{ text-align:center }}
</style>
</head>
<body>
<div class="container">
<h1>Node.js vs .NET vs Go – Realistic Performance Tests</h1>
<div class="grid">
{''.join(block(t) for t in RESULTS)}
</div>
</div>
<script>
{''.join(chart(t) for t in RESULTS)}
</script>
</body>
</html>
"""

    with open("results.html", "w") as f:
        f.write(html)

# ================= MAIN =================

async def main():
    await baseline_test()
    await cool_down(5)

    await io_test()
    await cool_down(10)

    await cpu_test()
    await cool_down(10)

    await sustained_test()

    print("\n===== FINAL SUMMARY =====")
    for test, data in RESULTS.items():
        print(f"\n{test}")
        for runtime, stats in data.items():
            print(f"  {runtime}: {stats}")

    generate_html()
    print("\n📄 HTML report generated → results.html")

if __name__ == "__main__":
    asyncio.run(main())
