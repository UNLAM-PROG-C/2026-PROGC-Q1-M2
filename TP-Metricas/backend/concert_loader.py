import json
import os
import logging
from database import get_cursor
from config import DATA_DIR

logger = logging.getLogger(__name__)

VALID_SECTIONS = ("campo", "platea", "platea_vip")


def load_concert_from_json(file_path: str) -> int:
    """Parse a concert JSON file and upsert it (concert + seats) into the DB."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    filename = os.path.basename(file_path)

    with get_cursor() as (cur, conn):
        cur.execute(
            """
            INSERT INTO concerts (name, artist, event_date, venue, description, json_file)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (json_file) DO UPDATE
                SET name        = EXCLUDED.name,
                    artist      = EXCLUDED.artist,
                    event_date  = EXCLUDED.event_date,
                    venue       = EXCLUDED.venue,
                    description = EXCLUDED.description
            RETURNING id
            """,
            (
                data["name"],
                data["artist"],
                data["event_date"],
                data["venue"],
                data.get("description", ""),
                filename,
            ),
        )
        concert_id = cur.fetchone()["id"]

        # Remove existing seats to allow clean reload
        cur.execute("DELETE FROM seats WHERE concert_id = %s", (concert_id,))

        seats_batch = []
        for section_name, section_cfg in data["sections"].items():
            if section_name not in VALID_SECTIONS:
                logger.warning(f"Sección desconocida ignorada: {section_name}")
                continue
            rows = section_cfg["rows"]
            per_row = section_cfg["seats_per_row"]
            price = section_cfg["price"]

            for row_num in range(1, rows + 1):
                row_label = chr(64 + row_num)  # 1→A, 2→B, …
                for seat_num in range(1, per_row + 1):
                    seats_batch.append(
                        (concert_id, section_name, row_label, str(seat_num), price)
                    )

        cur.executemany(
            """
            INSERT INTO seats (concert_id, section, row_label, seat_number, price)
            VALUES (%s, %s, %s, %s, %s)
            """,
            seats_batch,
        )

    logger.info(
        f"Recital cargado: '{data['name']}' — {len(seats_batch)} asientos (ID: {concert_id})"
    )
    return concert_id


def load_all_concerts():
    """Load every JSON file found in the data directory."""
    if not os.path.exists(DATA_DIR):
        logger.warning(f"Directorio de datos no encontrado: {DATA_DIR}")
        return

    json_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".json"))
    if not json_files:
        logger.warning("No se encontraron archivos JSON en el directorio de datos.")
        return

    for filename in json_files:
        try:
            load_concert_from_json(os.path.join(DATA_DIR, filename))
        except Exception as e:
            logger.error(f"Error cargando {filename}: {e}")
