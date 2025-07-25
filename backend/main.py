import os

from app import app
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
