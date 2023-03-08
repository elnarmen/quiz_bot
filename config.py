import os

from dotenv import load_dotenv


load_dotenv()


TG_TOKEN = os.getenv("TG_TOKEN")

REDIS_HOST = os.getenv("REDIS_HOST")

REDIS_PORT = os.getenv("REDIS_PORT")

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

QUESTIONS_PATH = os.path.join("quiz_questions", os.getenv("FILE_NAME"))
