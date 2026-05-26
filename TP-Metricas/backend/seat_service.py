from typing import List, Tuple, Dict
from database import get_pool, get_cursor
from config import RESERVATION_TIMEOUT_MINUTES
import race_logger
from ws_manager import manager as ws_manager


def get_concert_seats(concert_id: int) -> List[Dict]:
    with get_cursor(commit=False) as (cur, conn):
        cur.execute(
            """
            SELECT id, section, row_label, seat_number, status, price,
                   reserved_by, reserved_at, reservation_expires_at
            FROM seats
            WHERE concert_id = %s
            ORDER BY section, row_label, CAST(seat_number AS INTEGER)
            """,
            (concert_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def reserve_seats(
    seat_ids: List[int], user_id: int, username: str, concert_id: int
) -> Tuple[bool, str, List[Dict]]:
    """
    Atomically reserves one or more seats.

    Concurrency strategy: each UPDATE uses WHERE status='available' — the DB
    guarantees atomicity, so only one concurrent request per seat can succeed.
    If the returned rowcount is 0, a race condition occurred and we log it.

    If any seat in the batch fails, the whole transaction is rolled back so
    no partial reservations are left for this user.
    """
    reserved: List[Dict] = []
    p = get_pool()
    conn = p.getconn()

    try:
        with conn.cursor() as cur:
            for seat_id in seat_ids:
                # Fetch seat metadata for logging (inside same transaction)
                cur.execute(
                    """
                    SELECT s.section, s.row_label, s.seat_number, c.name AS concert_name
                    FROM seats s
                    JOIN concerts c ON c.id = s.concert_id
                    WHERE s.id = %s AND s.concert_id = %s
                    """,
                    (seat_id, concert_id),
                )
                row = cur.fetchone()
                info = dict(row) if row else None
                if not info:
                    conn.rollback()
                    return False, f"Asiento ID {seat_id} no encontrado en este recital.", []

                # ATOMIC reservation: only succeeds if status = 'available'
                # This WHERE clause is the primary race-condition guard
                cur.execute(
                    """
                    UPDATE seats
                    SET status                  = 'reserved',
                        reserved_by             = %s,
                        reserved_at             = NOW(),
                        reservation_expires_at  = NOW() + (%s * INTERVAL '1 minute')
                    WHERE id = %s AND concert_id = %s AND status = 'available'
                    RETURNING id, section, row_label, seat_number, price
                    """,
                    (user_id, RESERVATION_TIMEOUT_MINUTES, seat_id, concert_id),
                )
                result = cur.fetchone()

                if result is None:
                    # rowcount = 0 → race condition: another user got here first
                    label = (
                        f"{info['section'].upper()} "
                        f"{info['row_label']}{info['seat_number']}"
                    )
                    conn.rollback()
                    race_logger.log_race_condition(
                        seat_id=seat_id,
                        seat_label=label,
                        concert_name=info["concert_name"],
                        loser_username=username,
                        loser_user_id=user_id,
                    )
                    return (
                        False,
                        f"El asiento {label} ya fue seleccionado por otro usuario.",
                        [],
                    )

                reserved.append(dict(result))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)

    # Broadcast real-time update to all WebSocket clients watching this concert
    for seat in reserved:
        ws_manager.broadcast_from_thread(
            concert_id,
            {
                "type": "seat_reserved",
                "seat_id": seat["id"],
                "status": "reserved",
                "reserved_by": user_id,
            },
        )

    return True, "Asientos reservados exitosamente.", reserved


def release_seats(
    seat_ids: List[int], user_id: int, concert_id: int
) -> Tuple[bool, str]:
    with get_cursor() as (cur, conn):
        cur.execute(
            """
            UPDATE seats
            SET status                  = 'available',
                reserved_by             = NULL,
                reserved_at             = NULL,
                reservation_expires_at  = NULL
            WHERE id = ANY(%s) AND reserved_by = %s AND status = 'reserved'
            RETURNING id
            """,
            (seat_ids, user_id),
        )
        released_ids = [row["id"] for row in cur.fetchall()]

    for seat_id in released_ids:
        ws_manager.broadcast_from_thread(
            concert_id,
            {"type": "seat_released", "seat_id": seat_id, "status": "available"},
        )

    return True, f"{len(released_ids)} asiento(s) liberado(s)."


def confirm_purchase(
    seat_ids: List[int], user_id: int, concert_id: int
) -> Tuple[bool, str]:
    with get_cursor() as (cur, conn):
        cur.execute(
            """
            UPDATE seats
            SET status                  = 'sold',
                sold_at                 = NOW(),
                sold_to                 = %s,
                reserved_by             = NULL,
                reserved_at             = NULL,
                reservation_expires_at  = NULL
            WHERE id = ANY(%s) AND reserved_by = %s AND status = 'reserved'
            RETURNING id, section, row_label, seat_number, price
            """,
            (user_id, seat_ids, user_id),
        )
        sold = [dict(row) for row in cur.fetchall()]

    if len(sold) != len(seat_ids):
        return (
            False,
            "Algunos asientos no pudieron confirmarse (reserva expirada o inválida).",
        )

    total = sum(float(s["price"]) for s in sold)

    for seat in sold:
        ws_manager.broadcast_from_thread(
            concert_id,
            {"type": "seat_sold", "seat_id": seat["id"], "status": "sold"},
        )

    return True, f"Compra confirmada. {len(sold)} entrada(s). Total: ${total:.2f}"


def get_user_reserved_seats(user_id: int, concert_id: int) -> List[Dict]:
    with get_cursor(commit=False) as (cur, conn):
        cur.execute(
            """
            SELECT id, section, row_label, seat_number, price,
                   reservation_expires_at, status
            FROM seats
            WHERE reserved_by = %s AND concert_id = %s AND status = 'reserved'
            """,
            (user_id, concert_id),
        )
        return [dict(row) for row in cur.fetchall()]
