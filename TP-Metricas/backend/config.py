import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# Reservation timeout in minutes (configurable via env)
RESERVATION_TIMEOUT_MINUTES = int(os.getenv("RESERVATION_TIMEOUT_MINUTES", "5"))
PURCHASE_TIMEOUT_MINUTES = int(os.getenv("PURCHASE_TIMEOUT_MINUTES", "10"))

# Background cleanup interval
CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "30"))

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ticketdb")
DB_USER = os.getenv("DB_USER", "ticketuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ticketpass")
DB_MIN_CONNECTIONS = int(os.getenv("DB_MIN_CONNECTIONS", "5"))
DB_MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "20"))

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# Paths
DATA_DIR = os.path.join(ROOT_DIR, "data")
LOG_DIR = os.path.join(ROOT_DIR, "logs")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
RACE_CONDITION_LOG_FILE = os.path.join(LOG_DIR, "race_conditions.log")
