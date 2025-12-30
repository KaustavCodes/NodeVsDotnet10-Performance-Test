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
PYTHON = "http://localhost:8000"


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

SUTS = [
    ("Node.js", NODE),
    ("Dotnet", DOTNET),
    ("Go", GO),
    ("Dotnet AOT", DOTNET_AOT),
    ("Python", PYTHON)
]

async def baseline_test():
    print("\n--- ROUND 0: BASELINE (IO, SINGLE USER) ---")
    for name, base in SUTS:
        url = f"{base}/io"
        await warmup(url)
        lat, err = await run_test("Baseline", name, url, concurrency=1)
        RESULTS["Baseline"][name] = summarize(lat, err)

async def io_test():
    print("\n--- ROUND 1: IO-BOUND (ASYNC SCALABILITY) ---")
    for name, base in SUTS:
        url = f"{base}/io"
        await warmup(url)
        lat, err = await run_test("IO", name, url, concurrency=200)
        RESULTS["IO"][name] = summarize(lat, err)

async def cpu_test():
    print("\n--- ROUND 2: CPU-BOUND (PRIME CALCULATION) ---")
    for name, base in SUTS:
        url = f"{base}/heavy"
        await warmup(url)
        lat, err = await run_test("CPU", name, url, concurrency=4)
        RESULTS["CPU"][name] = summarize(lat, err)

async def sustained_test():
    print("\n--- ROUND 3: SUSTAINED LOAD (TAIL LATENCY) ---")
    for name, base in SUTS:
        url = f"{base}/io"
        await warmup(url)
        lat, err = await run_test("Sustained", name, url, concurrency=300)
        RESULTS["Sustained"][name] = summarize(lat, err)

# ================= HTML REPORT =================

def generate_html():
    # Helper to restructure data for charts
    def get_metric(metric_name):
        return {test: {runtime: data.get(runtime, {}).get(metric_name) for runtime in [s[0] for s in SUTS]} for test, data in RESULTS.items()}
    
    # Generate cards HTML
    cards_html = ""
    for test in RESULTS:
        stats_avg_html = ""
        stats_err_html = ""
        for lang, _ in SUTS:
            stats_avg_html += f"""
            <div class="stat-item">
                <span class="stat-label">{lang} Avg</span>
                <span class="stat-val">{fmt(RESULTS[test][lang]['avg'])}s</span>
            </div>"""
            
            err_count = RESULTS[test][lang]['errors']
            err_color = '#ef4444' if err_count > 0 else '#4ade80'
            stats_err_html += f"""
            <div class="stat-item">
                <span class="stat-label">{lang} Err</span>
                <span class="stat-val" style="color: {err_color}">{err_count}</span>
            </div>"""

        cards_html += f"""
        <div class="card">
            <h2>{test}</h2>
            <canvas id="{test}Chart"></canvas>
            <div class="stats-grid">
                {stats_avg_html}
            </div>
             <div class="stats-grid" style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
                {stats_err_html}
            </div>
        </div>
        """

    # Generate scripts
    scripts = ""
    colors = {
        'Node.js': '#68a063',
        'Dotnet': '#512bd4',
        'Go': '#00ADD8',
        'Dotnet AOT': '#d946ef',
        'Python': '#FFD43B'
    }
    
    for test in RESULTS:
        labels = [s[0] for s in SUTS]
        data_vals = [RESULTS[test][lang]['avg'] for lang in labels]
        bg_colors = [colors.get(l, '#ccc') for l in labels]
        
        scripts += f"""
        new Chart(document.getElementById('{test}Chart'), {{
            type: 'bar',
            data: {{
                labels: {str(labels)},
                datasets: [{{
                    label: 'Avg Latency (s)',
                    data: {str(data_vals)},
                    backgroundColor: {str(bg_colors)},
                    borderRadius: 6,
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: '#1e293b',
                        padding: 12,
                        titleFont: {{ size: 14 }},
                        bodyFont: {{ size: 13 }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                        ticks: {{ color: '#94a3b8' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#94a3b8' }}
                    }}
                }}
            }}
        }});
        """

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Benchmark Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #3b82f6; --bg: #0f172a; --card-bg: #1e293b; --text: #f8fafc; --text-dim: #94a3b8; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 40px 20px; }}
        .container {{ max-width: 1200px; margin: auto; }}
        h1 {{ text-align: center; font-weight: 800; font-size: 2.5rem; margin-bottom: 40px; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 30px; }}
        .card {{ background: var(--card-bg); padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid rgba(255,255,255,0.05); }}
        h2 {{ margin-top: 0; font-size: 1.5rem; color: var(--primary); border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; margin-top: 20px; font-size: 0.9rem; }}
        .stat-item {{ background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; text-align: center; }}
        .stat-label {{ color: var(--text-dim); font-size: 0.75rem; display: block; margin-bottom: 4px; }}
        .stat-val {{ font-weight: 600; }}
        canvas {{ max-height: 300px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Benchmark Results: Node vs .NET vs Go vs Python</h1>
        <div class="grid">
            {cards_html}
        </div>
    </div>

    <script>
        {scripts}
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

