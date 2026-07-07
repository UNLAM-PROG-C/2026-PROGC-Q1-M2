import logging
import threading
import os
from config import RACE_CONDITION_LOG_FILE, LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)

_logger = logging.getLogger("race_conditions")
_logger.setLevel(logging.INFO)
_logger.propagate = False

_file_handler = logging.FileHandler(RACE_CONDITION_LOG_FILE, encoding="utf-8")
_file_handler.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
_file_handler.setFormatter(_fmt)
_logger.addHandler(_file_handler)

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_fmt)
_logger.addHandler(_console_handler)


def log_race_condition(
    seat_id: int,
    seat_label: str,
    concert_name: str,
    loser_username: str,
    loser_user_id: int,
):
    """
    Logs a detected race condition to file and DB.
    Called when a seat reservation attempt returns rowcount=0
    (seat already taken).
    """
    thread_name = threading.current_thread().name
    _logger.info(
        f"[RACE_CONDITION] Seat ID:{seat_id} ({seat_label}) "
        f"of concert '{concert_name}' - "
        f"User '{loser_username}' (ID:{loser_user_id}) tried to reserve a seat "
        f"already taken by another user. Only 1 user got the seat. "
        f"Thread: {thread_name}"
    )

    # Persist to DB (imported inside the function to avoid a circular import)
    try:
        from database import get_cursor

        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO race_condition_log
                    (seat_id, loser_user_id, loser_username, thread_name)
                VALUES (%s, %s, %s, %s)
                """,
                (seat_id, loser_user_id, loser_username, thread_name),
            )
    except Exception as e:
        _logger.error(f"Error persisting race condition to DB: {e}")
