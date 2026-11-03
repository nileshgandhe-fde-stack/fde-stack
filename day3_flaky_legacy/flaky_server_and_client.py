import asyncio
import random
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type

# --- Simple Stateful Circuit Breaker ---
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 5.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = 0.0

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            print(f"🚨 [CIRCUIT BREAKER] Tripped to OPEN after {self.failures} consecutive failures!")

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN" and (time.time() - self.last_failure_time) > self.recovery_timeout:
            self.state = "HALF_OPEN"
            print("🟡 [CIRCUIT BREAKER] Moving to HALF_OPEN probe state...")
            return True
        return False

breaker = CircuitBreaker(failure_threshold=4, recovery_timeout=3.0)

# --- Mock Flaky Legacy Enterprise Endpoint ---
async def mock_legacy_erp_handler(request: httpx.Request) -> httpx.Response:
    roll = random.random()
    if roll < 0.25:
        return httpx.Response(503, json={"error": "Legacy Mainframe Pool Busy"})
    elif roll < 0.40:
        return httpx.Response(429, headers={"Retry-After": "1"}, json={"error": "Rate limit exceeded"})
    return httpx.Response(200, json={"page": str(request.url), "claims_synced": 50, "status": "OK"})

# --- Fault-Tolerant FDE Poller with Tenacity ---
@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_random_exponential(multiplier=0.5, max=4.0),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError))
)
async def fetch_page_with_retry(client: httpx.AsyncClient, page_num: int):
    if not breaker.allow_request():
        await asyncio.sleep(3.1)  # Wait for breaker cool-down
    
    resp = await client.get(f"https://legacy-erp.internal/api/claims?page={page_num}")
    if resp.status_code in (429, 500, 502, 503, 504):
        breaker.record_failure()
        print(f"⚠️  Page {page_num} failed with HTTP {resp.status_code} -> Retrying with backoff+jitter...")
        resp.raise_for_status()
    
    breaker.record_success()
    return resp.json()

async def main():
    transport = httpx.MockTransport(mock_legacy_erp_handler)
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    
    async with httpx.AsyncClient(transport=transport, limits=limits, timeout=5.0) as client:
        for page in range(1, 16):
            result = await fetch_page_with_retry(client, page)
            print(f"✅ Page {page:02d} synced successfully | Breaker State: {breaker.state} | {result}")

if __name__ == "__main__":
    asyncio.run(main())