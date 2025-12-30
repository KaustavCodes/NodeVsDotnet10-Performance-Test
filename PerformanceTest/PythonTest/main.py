import time
import math
from fastapi import FastAPI
import uvicorn

app = FastAPI()

def get_nth_prime(n: int) -> int:
    count = 0
    num = 2
    while count < n:
        is_prime = True
        sqrt_num = int(math.isqrt(num))
        for i in range(2, sqrt_num + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
        if count < n:
            num += 1
    return num

@app.get("/io")
async def io_handler():
    # Simulate I/O delay
    time.sleep(0.1) # 100ms
    return {
        "Message": "I/O Operation Complete",
        "Platform": "Python (FastAPI)"
    }

@app.get("/heavy")
async def heavy_handler():
    start = time.perf_counter()
    nth = 20000
    prime = get_nth_prime(nth)
    duration = (time.perf_counter() - start) * 1000

    return {
        "Message": f"Found {nth}th prime number",
        "Result": prime,
        "DurationMs": duration,
        "Platform": "Python (FastAPI)"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
