import random
import logging

import redis
import telegram
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from environs import Env
from pathlib import Path

from questions_answers_utils import (
    parce_questions,
    check_user_answer,
)
from logs_handler import TelegramLogsHandler


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


def send_message(event, vk_api, messaage):
    vk_api.messages.send(
        user_id=event.user_id,
        message=messaage,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def quiz_handler(event, vk_api, redis_connection, questions_with_answers):
    if event.text == "Новый вопрос":
        question = random.choice(list(questions_with_answers.keys()))
        redis_connection.set(event.user_id, question)
        send_message(event, vk_api, messaage=question)
    elif event.text == "Сдаться":
        question = redis_connection.get(event.user_id)
        correct_answer = questions_with_answers.get(question)
        send_message(event, vk_api, messaage=correct_answer)
    else:
        question = redis_connection.get(event.user_id)
        user_answer = event.text
        correct_answer = questions_with_answers.get(question)

        if check_user_answer(user_answer, correct_answer):
            message = "Правильно! Поздравляю! "
            "Для следующего вопроса нажми «Новый вопрос»"
            send_message(event, vk_api, message)
        else:
            message = "Неправильно… Попробуешь ещё раз?"
            send_message(event, vk_api, message)


if __name__ == "__main__":
    env = Env()
    env.read_env()

    QUESTIONS_PATH = Path(
        BASE_DIR,
        "quiz_questions",
        env("FILE_NAME", default="questions.txt")
    )

    logs_telegram_bot = telegram.Bot(token=env("LOGGER_TG_TOKEN"))
    logger.setLevel(logging.ERROR)
    logger.addHandler(TelegramLogsHandler(logs_telegram_bot, env("LOGS_CHAT_ID")))

    vk_session = vk.VkApi(token=env("VK_TOKEN"))
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)

    redis_host = env("REDIS_HOST")
    redis_port = env("REDIS_PORT")
    redis_password = env("REDIS_PASSWORD")
    redis_connection = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        password=redis_password,
        decode_responses=True
    )

    questions_with_answers = parce_questions(QUESTIONS_PATH)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                quiz_handler(
                    event,
                    vk_api,
                    redis_connection,
                    questions_with_answers
                )
            except Exception as err:
                logger.exception(err)
