import asyncio
import random
import time
from typing import Dict

# Simulated payment gateway latency range (seconds)
MIN_PAYMENT_LATENCY_SECONDS = 0.3
MAX_PAYMENT_LATENCY_SECONDS = 0.8
# Used to derive a millisecond-based transaction id
MILLISECONDS_PER_SECOND = 1000


async def process_payment(user_id: int, amount: float, payment_method: str = "credit_card") -> Dict:
    """
    Payment stub: simulates an external payment gateway.
    Always returns success. asyncio.sleep simulates network latency
    without blocking a thread from FastAPI's thread pool.
    Replace this with a real payment provider integration in production.
    """
    await asyncio.sleep(random.uniform(MIN_PAYMENT_LATENCY_SECONDS, MAX_PAYMENT_LATENCY_SECONDS))

    return {
        "success": True,
        "transaction_id": f"TXN-{user_id}-{int(time.time() * MILLISECONDS_PER_SECOND)}",
        "amount": amount,
        "payment_method": payment_method,
        "message": "Pago procesado exitosamente (STUB - simulación)",
        "stub": True,
    }
