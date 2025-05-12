from dotenv import load_dotenv
from pathlib import Path

print(load_dotenv(dotenv_path=Path(__file__).parent / ".env")) 