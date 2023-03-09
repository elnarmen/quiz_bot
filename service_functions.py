import re
from string import punctuation

import redis

from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD


def parce_questions(path: str) -> dict:
    with open(path, "r", encoding="KOI8-R") as file:
        content = file.read()
    questions_descriptions = content.split("\n\n")

    questions = []
    answers = []

    for part in questions_descriptions:
        if "Вопрос" in part:
            questions.append(part.split(":\n")[1].replace("\n", " "))
        if "Ответ" in part:
            answers.append(part.split(":\n")[1].strip().replace("\n", " "))
    return dict(zip(questions, answers))


def leave_only_letters(text):
    new_string = ''.join([char for char in text if char not in punctuation])
    # удаляем лишние пробелы
    new_string = ' '.join(new_string.split())
    return new_string


def check_user_answer(user_answer, correct_answer):
    matches = re.search(r"^[^.()]+", correct_answer)
    if leave_only_letters(user_answer.lower()) ==\
            leave_only_letters(matches.group().lower()):
        return True


def connect_db():
    redis_host = REDIS_HOST
    redis_port = REDIS_PORT
    redis_password = REDIS_PASSWORD

    return redis.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        password=redis_password,
        decode_responses=True
    )
