import os

from environs import Env

env = Env()
env.read_env()


TG_TOKEN = env("TG_TOKEN")

VK_TOKEN = env("VK_TOKEN")

REDIS_HOST = env("REDIS_HOST")

REDIS_PORT = env("REDIS_PORT")

REDIS_PASSWORD = env("REDIS_PASSWORD")

QUESTIONS_PATH = os.path.join(
    "quiz_questions",
    env("FILE_NAME", default="1vs1200.txt")
)
