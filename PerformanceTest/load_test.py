import requests
import threading
import time
import json
import statistics
import sys
import random

# Configuration
NODE_BASE = "http://localhost:3000"
DOTNET_BASE = "http://localhost:5500"

# CPU TEST CONFIG
CPU_CONCURRENCY = 200
CPU_REQUESTS = 25 
EXPECTED_PRIME = 224737

# I/O TEST CONFIG
IO_CONCURRENCY = 1000
IO_REQUESTS = 20

# ATTACK TEST CONFIG
ATTACK_CONCURRENCY = 2000
ATTACK_REQUESTS = 50

results = {
    "CPU": {
        "Node.js": {"times": [], "errors": 0, "mismatches": 0},
        "Dotnet": {"times": [], "errors": 0, "mismatches": 0}
    },
    "IO": {
        "Node.js": {"times": [], "errors": 0},
        "Dotnet": {"times": [], "errors": 0}
    },
    "Attack": {
        "Node.js": {"times": [], "errors": 0},
        "Dotnet": {"times": [], "errors": 0}
    }
}


def cool_down(seconds=5):
    print(f"\n❄️  Cooling down for {seconds} seconds...")
    time.sleep(seconds)
    print("🔥  Ready!\n")

def warm_up(url, platform):
    print(f"\n☀️  Warming up {platform} ({url})...")
    try:
        # Simple sequential requests to wake up the server
        for _ in range(10):
            requests.get(url, timeout=5)
    except Exception as e:
        print(f"⚠️  Warmup warning for {platform}: {e}")
    print("🔥  Warmup complete!\n")

def run_load(url, platform, category, concurrency, requests_per_thread, check_prime=False, ramp_up_time=0, attack_mode=False):
    total_requests = concurrency * requests_per_thread
    print(f"[{category}] {platform}: Starting {concurrency} threads x {requests_per_thread} reqs ({total_requests} total)")
    if ramp_up_time > 0 and not attack_mode:
        print(f"   (Ramping up over {ramp_up_time}s)")
    if attack_mode:
        print(f"   (⚔️  ATTACK MODE: No Mercy! No Delays!)")
    
    threads = []
    completed_lock = threading.Lock()
    completed_count = 0
    
    def worker():
        nonlocal completed_count
        # Use a Session for connection pooling (Keep-Alive)
        session = requests.Session()
        # Mimic a browser
        session.headers.update({
            "User-Agent": "PerformanceTest/1.0",
            "Connection": "keep-alive"
        })
        
        for _ in range(requests_per_thread):
            start = time.time()
            try:
                resp = session.get(url, timeout=30)
                if resp.status_code == 200:
                    duration = time.time() - start
                    results[category][platform]["times"].append(duration)
                    
                    if check_prime:
                        data = resp.json()
                        if data.get("result") != EXPECTED_PRIME:
                            results[category][platform]["mismatches"] += 1
                else:
                    results[category][platform]["errors"] += 1
            except Exception:
                results[category][platform]["errors"] += 1
            
            with completed_lock:
                completed_count += 1
            
            # Simulate "Think Time" (random pause between requests)
            # ONLY if NOT in attack mode
            if not attack_mode:
                time.sleep(random.uniform(0.1, 0.5))
        
        session.close()

    # Start threads 
    # Disable ramp-up if attack mode (Shock the system)
    delay_per_thread = (ramp_up_time / concurrency) if (ramp_up_time > 0 and not attack_mode) else 0
    
    for _ in range(concurrency):
        t = threading.Thread(target=worker)
        t.daemon = True
        threads.append(t)
        t.start()
        if delay_per_thread > 0:
            time.sleep(delay_per_thread)
    
    # Monitor progress
    while completed_count < total_requests:
        time.sleep(0.1)
        percent = (completed_count / total_requests) * 100
        bar_length = 30
        filled_length = int(bar_length * completed_count // total_requests)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        sys.stdout.write(f'\r[{category}] {platform} |{bar}| {percent:.1f}% ({completed_count}/{total_requests})')
        sys.stdout.flush()
        
        # Check if all threads died unexpectedly (simple check)
        if not any(t.is_alive() for t in threads) and completed_count < total_requests:
            break

    # Final join
    for t in threads:
        t.join()
    
    # Final print to clear line
    sys.stdout.write(f'\r[{category}] {platform} |{"█"*30}| 100.0% ({total_requests}/{total_requests}) ✅\n')
    sys.stdout.flush()

def generate_html_report():
    def get_avg(cat, plat):
        data = results[cat][plat]["times"]
        return statistics.mean(data) if data else 0

    def get_errors(cat, plat):
        return results[cat][plat]["errors"]

    cpu_node = get_avg("CPU", "Node.js")
    cpu_dotnet = get_avg("CPU", "Dotnet")
    io_node = get_avg("IO", "Node.js")
    io_dotnet = get_avg("IO", "Dotnet")
    attack_node = get_avg("Attack", "Node.js")
    attack_dotnet = get_avg("Attack", "Dotnet")

    attack_err_node = get_errors("Attack", "Node.js")
    attack_err_dotnet = get_errors("Attack", "Dotnet")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Node.js vs .NET: The Ultimate Battle</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; padding: 20px; background: #f0f2f5; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #1a1a1a; margin-bottom: 30px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px; }}
            .chart-card {{ padding: 20px; border-radius: 8px; background: #fff; border: 1px solid #e1e4e8; }}
            h2 {{ text-align: center; font-size: 1.2rem; color: #444; }}
            .stats {{ margin-top: 10px; font-size: 0.9rem; color: #666; text-align: center; }}
            .error-stats {{ color: #dc3545; font-weight: bold; font-size: 0.8rem; margin-top: 5px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Performance Showdown</h1>
            
            <div class="grid">
                <div class="chart-card">
                    <h2>Round 1: CPU Heavy (Prime Calc)</h2>
                    <canvas id="cpuChart"></canvas>
                    <div class="stats">
                        Node: {cpu_node:.4f}s | .NET: {cpu_dotnet:.4f}s
                    </div>
                </div>
                <div class="chart-card">
                    <h2>Round 2: I/O Bound (Simulated Wait)</h2>
                    <canvas id="ioChart"></canvas>
                    <div class="stats">
                        Node: {io_node:.4f}s | .NET: {io_dotnet:.4f}s
                    </div>
                </div>
                <div class="chart-card" style="grid-column: span 2;">
                    <h2>Round 3: ATTACK MODE (Stress Test)</h2>
                    <canvas id="attackChart"></canvas>
                    <div class="stats">
                        Node: {attack_node:.4f}s | .NET: {attack_dotnet:.4f}s
                    </div>
                    <div class="error-stats">
                        Failed Reqs -> Node: {attack_err_node} | .NET: {attack_err_dotnet}
                    </div>
                </div>
            </div>
        </div>
        <script>
            const createChart = (ctx, label, nodeVal, netVal) => {{
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Node.js', '.NET'],
                        datasets: [{{
                            label: 'Avg Response (s)',
                            data: [nodeVal, netVal],
                            backgroundColor: ['#68a063', '#512bd4']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: 'Seconds (Lower is Better)' }} }} }}
                    }}
                }});
            }};

            createChart(document.getElementById('cpuChart'), 'CPU', {cpu_node}, {cpu_dotnet});
            createChart(document.getElementById('ioChart'), 'I/O', {io_node}, {io_dotnet});
            createChart(document.getElementById('attackChart'), 'Attack', {attack_node}, {attack_dotnet});
        </script>
    </body>
    </html>
    """
    
    with open("results.html", "w") as f:
        f.write(html_content)
    print("Results generated: results.html")

if __name__ == "__main__":
    # CPU Round
    print("--- ROUND 1: CPU HEAVY BOUND ---")
    warm_up(f"{NODE_BASE}/heavy", "Node.js")
    run_load(f"{NODE_BASE}/heavy", "Node.js", "CPU", CPU_CONCURRENCY, CPU_REQUESTS, True)
    
    cool_down(3)
    
    warm_up(f"{DOTNET_BASE}/heavy", "Dotnet")
    run_load(f"{DOTNET_BASE}/heavy", "Dotnet", "CPU", CPU_CONCURRENCY, CPU_REQUESTS, True)

    cool_down(10) # Longer cooldown before the massive connection storm

    # I/O Round with Ramp-up
    print("--- ROUND 2: I/O BOUND (HIGH CONCURRENCY) ---")
    
    warm_up(f"{NODE_BASE}/io", "Node.js")
    # Using 5s ramp-up for 1000 users = 200 users/sec
    run_load(f"{NODE_BASE}/io", "Node.js", "IO", IO_CONCURRENCY, IO_REQUESTS, ramp_up_time=5)
    
    cool_down()
    
    warm_up(f"{DOTNET_BASE}/io", "Dotnet")
    run_load(f"{DOTNET_BASE}/io", "Dotnet", "IO", IO_CONCURRENCY, IO_REQUESTS, ramp_up_time=5)
    
    cool_down(10)

    # Attack Round
    print("--- ROUND 3: ATTACK MODE (NO MERCY) ---")
    
    warm_up(f"{NODE_BASE}/io", "Node.js")
    run_load(f"{NODE_BASE}/io", "Node.js", "Attack", ATTACK_CONCURRENCY, ATTACK_REQUESTS, attack_mode=True)
    
    cool_down()
    
    warm_up(f"{DOTNET_BASE}/io", "Dotnet")
    run_load(f"{DOTNET_BASE}/io", "Dotnet", "Attack", ATTACK_CONCURRENCY, ATTACK_REQUESTS, attack_mode=True)

    generate_html_report()
