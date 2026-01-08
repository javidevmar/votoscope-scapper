import os
from dotenv import load_dotenv

load_dotenv()

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
LOGGING_FORMAT = os.getenv("LOGGING_FORMAT", "%(asctime)s [%(levelname)s] %(message)s")
