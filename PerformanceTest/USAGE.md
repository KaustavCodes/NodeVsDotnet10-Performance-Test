# 🚀 Usage Guide: Node.js vs .NET vs Go vs Python Performance Tests

This guide explains how to run the multi-language performance benchmark suite. The tests require running separate backend servers for each language and then executing the main load test script.

## 📋 Prerequisites
- **Node.js**: v18+
- **.NET SDK**: v8.0+
- **Go**: v1.20+
- **Python**: v3.9+ (`pip install fastapi uvicorn aiohttp numpy tqdm`)

## 1️⃣ Start the Backend Servers

You need to run all five servers in separate terminal windows/tabs.

### Node.js (Port 3000)
```bash
cd PerformanceTest/NodeJstest
node index.js
```

### .NET Standard (Port 5500)
```bash
cd PerformanceTest/DotnetTest/DotnetTest
dotnet run
```

### .NET AOT (Port 5600)
```bash
cd PerformanceTest/DotnetAot/DotnetAotTest
dotnet run
```

### Go (Port 8080)
```bash
cd PerformanceTest/GoLangTEst
go run main.go
```

### Python (Port 8000)
```bash
cd PerformanceTest/PythonTest
# Make sure uvicorn is installed: pip install fastapi uvicorn
python3 -m uvicorn main:app --port 8000 --host 0.0.0.0
```

## 2️⃣ Run the Load Test

Once all servers are up and running, execute the main benchmark script.

```bash
cd PerformanceTest
# Make sure dependencies are installed: pip install aiohttp numpy tqdm
python3 load_test.py
```

## 3️⃣ View Results

After the test completes:
1. Console output will show a summary of latencies and error counts.
2. A detailed **HTML Report** is generated at `PerformanceTest/results.html`.
3. Open `results.html` in your browser to view the interactive dashboard.

---

## 🛠️ Configuration
You can modify test parameters in `PerformanceTest/load_test.py`:
- `TEST_DURATION`: Duration of each test phase (default: 30s)
- `WARMUP_DURATION`: Warmup time before measuring (default: 5s)
- `SUTS`: List of systems under test (comment out any you don't want to test)
