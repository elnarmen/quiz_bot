import logging
import os
from random import choice
from pathlib import Path

import redis
import telegram
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CallbackContext, CommandHandler
from telegram.ext import MessageHandler, Filters, ConversationHandler
from environs import Env
from pathlib import Path

from questions_answers_utils import parce_questions, check_user_answer
from logs_handler import TelegramLogsHandler


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


def get_keyboard():
    keyboard = [
        ["Новый вопрос", "Сдаться"],
    ]
    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return markup


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет, я бот для викторины",
        reply_markup=get_keyboard()
    )


def handle_new_question_request(update: Update, context: CallbackContext):
    db_connection = context.bot_data["redis_connection"]
    question = choice(list(context.bot_data["questions_with_answers"].keys()))

    db_connection.set(update.message.chat_id, question)
    update.message.reply_text(question)


def handle_solution_attempt(update: Update, context: CallbackContext):
    db_connection = context.bot_data["redis_connection"]
    question = db_connection.get(update.message.chat_id)
    user_answer = update.message.text
    correct_answer = context.bot_data["questions_with_answers"].get(question)

    if check_user_answer(user_answer, correct_answer):
        update.message.reply_text(
            "Правильно! Поздравляю! "
            "Для следующего вопроса нажми «Новый вопрос»",
            reply_markup=get_keyboard()
        )
    else:
        update.message.reply_text(
            "Неправильно… Попробуешь ещё раз?",
            reply_markup=get_keyboard()
        )


def send_correct_answer(update: Update, context: CallbackContext):
    user_id = update.effective_user["id"]
    question = context.bot_data["redis_connection"].get(user_id)
    correct_answer = context.bot_data["questions_with_answers"].get(question)
    update.message.reply_text(correct_answer)
    return handle_new_question_request(update, context)


def stop(update: Update, context: CallbackContext):
    update.message.reply_text(
        'До встречи!',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def error_handler(update: Update, context: CallbackContext):
    logger.exception(context.error)


def main():
    env = Env()
    env.read_env()

    QUESTIONS_PATH = Path(
        BASE_DIR,
        "quiz_questions",
        env("FILE_NAME", default="questions.txt")
    )

    logs_bot = telegram.Bot(token=env("LOGGER_TG_TOKEN"))
    logger.setLevel(logging.ERROR)
    logger.addHandler(TelegramLogsHandler(logs_bot, env("LOGS_CHAT_ID")))

    updater = Updater(env("TG_TOKEN"))
    dispatcher = updater.dispatcher

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

    dispatcher.bot_data["redis_connection"] = redis_connection
    dispatcher.bot_data["questions_with_answers"] = questions_with_answers

    dispatcher.add_error_handler(error_handler)

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(
        MessageHandler(
            Filters.regex("^Новый вопрос"),
            handle_new_question_request
        ),
    )

    dispatcher.add_handler(
        MessageHandler(Filters.regex("^Сдаться"), send_correct_answer),
    )

    dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            handle_solution_attempt
        )
    )

    dispatcher.add_handler(CommandHandler("stop", stop))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
