// http_spam.js
const http = require('http');

const TARGET_URL = 'http://127.0.0.1:3000/api/telemetry'; // Adjust port/route per portal
const TOTAL_REQUESTS = 1000;
const CONCURRENT_BATCH = 50;

async function fireRequest(id) {
 return new Promise((resolve) => {
 const payload = JSON.stringify({ deviceId: `STRESS_TEST_${id}`, val: 42 });
 
 const req = http.request(TARGET_URL, {
 method: 'POST',
 headers: {
 'Content-Type': 'application/json',
 'Content-Length': Buffer.byteLength(payload)
 }
 }, (res) => {
 let data = '';
 res.on('data', chunk => data += chunk);
 res.on('end', () => resolve(res.statusCode));
 });

 req.on('error', () => resolve(500));
 req.write(payload);
 req.end();
 });
}

async function runTest() {
 console.log(`Blasting ${TARGET_URL} with ${TOTAL_REQUESTS} requests...`);
 const start = Date.now();
 let statusCounts = {};

 for (let i = 0; i < TOTAL_REQUESTS; i += CONCURRENT_BATCH) {
 const batch = Array.from({ length: CONCURRENT_BATCH }, (_, idx) => fireRequest(i + idx));
 const results = await Promise.all(batch);
 
 results.forEach(code => {
 statusCounts[code] = (statusCounts[code] || 0) + 1;
 });
 }

 const duration = (Date.now() - start) / 1000;
 console.log(`--- Stress Test Summary ---`);
 console.log(`Duration: ${duration.toFixed(2)}s`);
 console.log(`Requests per second: ${(TOTAL_REQUESTS / duration).toFixed(1)}`);
 console.log(`Response Status Distributions:`, statusCounts);
 console.log(`Note: You should see a large volume of 429 (Too Many Requests) if SecOps rate-limiting is working sweet as.`);
}

runTest();
