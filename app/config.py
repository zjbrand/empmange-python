import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///" +
                         (BASE_DIR/"empmanage.db").as_posix())
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))).resolve()
MAX_IMAGE_BYTES = 5 * 1024 * 1024
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
