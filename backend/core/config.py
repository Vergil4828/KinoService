import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

script_dir = Path(__file__).parent
backend_root = script_dir.parent
top_level_root = backend_root.parent

dotenv_path = top_level_root / ".env"
load_dotenv(dotenv_path=dotenv_path)

PUBLIC_DIR = top_level_root / "public"
if not PUBLIC_DIR.exists():
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Создана директория: {PUBLIC_DIR}")


AVATAR_UPLOAD_DIR = PUBLIC_DIR / "uploads" / "avatars"
if not AVATAR_UPLOAD_DIR.exists():
    AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Создана директория для аватаров: {AVATAR_UPLOAD_DIR}")


PORT = int(os.getenv("PORT", 8000))
if not os.getenv("PORT"):
    logger.warning(
        "Переменная окружения PORT не установлена, используется по умолчанию 8000."
    )

ALLOWED_ORIGINS = [
    "https://vosmerka228.ru",
    "https://api.vosmerka228.ru",
    "http://localhost:5173",
    "https://m.vosmerka228.ru",
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
]

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    parsed_url = urlparse(DATABASE_URL)
    MONGO_URI = DATABASE_URL
    MONGO_DB_NAME = parsed_url.path.strip("/") or os.getenv("MONGO_DB_NAME")
else:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")


if not MONGO_URI:
    logger.error("Переменная окружения MONGO_URI не установлена!")
    exit(1)
if not MONGO_DB_NAME:
    logger.warning(
        "Переменная окружения MONGO_DB_NAME не установлена. База данных будет выбрана из URI."
    )


JWT_SECRET_KEY = os.getenv("JWT_SECRET")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

if not JWT_SECRET_KEY:
    logger.error("Переменная окружения JWT_SECRET не установлена!")
    exit(1)
if not REFRESH_SECRET_KEY:
    logger.error("Переменная окружения REFRESH_SECRET не установлена!")
    exit(1)
