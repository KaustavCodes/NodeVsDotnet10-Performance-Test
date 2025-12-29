const http = require('http');

const PORT = 3000;

// Function to calculate nth prime number (CPU intensive)
const getNthPrime = (n) => {
    let count = 0;
    let num = 2;
    while (count < n) {
        let isPrime = true;
        for (let i = 2; i <= Math.sqrt(num); i++) {
            if (num % i === 0) {
                isPrime = false;
                break;
            }
        }
        if (isPrime) {
            count++;
        }
        if (count < n) {
            num++;
        }
    }
    return num;
};

const server = http.createServer((req, res) => {
    if (req.url === '/heavy' && req.method === 'GET') {
        const start = process.hrtime();
        const nth = 20000; // Calculate 20,000th prime
        const prime = getNthPrime(nth);
        const end = process.hrtime(start);
        const durationMs = (end[0] * 1000 + end[1] / 1e6).toFixed(2);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            message: `Found ${nth}th prime number`,
            result: prime,
            durationMs: durationMs,
            platform: 'Node.js'
        }));
    } else if (req.url === '/io' && req.method === 'GET') {
        // Simulate I/O delay (e.g., DB query)
        setTimeout(() => {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                message: 'I/O Operation Complete',
                platform: 'Node.js'
            }));
        }, 100);
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    }
});

server.listen(PORT, () => {
    console.log(`Node.js server running on port ${PORT}`);
});
