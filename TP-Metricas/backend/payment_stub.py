import time
import random
from typing import Dict


def process_payment(user_id: int, amount: float, payment_method: str = "credit_card") -> Dict:
    """
    Payment stub: simulates an external payment gateway.
    Always returns success. A small sleep simulates network latency.
    Replace this with a real payment provider integration in production.
    """
    time.sleep(random.uniform(0.3, 0.8))

    return {
        "success": True,
        "transaction_id": f"TXN-{user_id}-{int(time.time() * 1000)}",
        "amount": amount,
        "payment_method": payment_method,
        "message": "Pago procesado exitosamente (STUB - simulación)",
        "stub": True,
    }
