import logging
import os
import re
from string import punctuation
from random import choice
from pathlib import Path

import redis
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CallbackContext, CommandHandler
from telegram.ext import MessageHandler, Filters, ConversationHandler

from config import TG_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, QUESTIONS_PATH
from questions import parce_questions

logger = logging.getLogger(__name__)

USER_CHOICE = range(1)


def leave_only_letters(text):
    new_string = ''.join([char for char in text if char not in punctuation])
    # удаляем лишние пробелы
    new_string = ' '.join(new_string.split())
    return new_string


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

    return USER_CHOICE


def handle_new_question_request(update: Update, context: CallbackContext):
    db_connection = context.bot_data["redis_connection"]
    question = choice(list(context.bot_data["questions_with_answers"].keys()))

    db_connection.set(update.message.chat_id, question)
    update.message.reply_text(question)
    return USER_CHOICE


def handle_solution_attempt(update: Update, context: CallbackContext):
    db_connection = context.bot_data["redis_connection"]
    question = db_connection.get(update.message.chat_id)
    user_answer = update.message.text

    correct_answer = context.bot_data["questions_with_answers"].get(question)
    matches = re.search(r"^[^.()]+", correct_answer)
    if leave_only_letters(user_answer.lower()) ==\
            leave_only_letters(matches.group().lower()):

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

    return USER_CHOICE


def stop(update: Update, context: CallbackContext):
    update.message.reply_text(
        'До встречи!',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def send_correct_answer(update: Update, context: CallbackContext):
    user_id = update.effective_user["id"]
    question = context.bot_data["redis_connection"].get(user_id)
    correct_answer = context.bot_data["questions_with_answers"].get(question)
    update.message.reply_text(correct_answer)
    return handle_new_question_request(update, context)


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    updater = Updater(TG_TOKEN)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            USER_CHOICE: [
                MessageHandler(
                    Filters.regex("^Новый вопрос"),
                    handle_new_question_request
                ),
                MessageHandler(Filters.regex("^Сдаться"), send_correct_answer),
                MessageHandler(
                    Filters.text & ~Filters.command,
                    handle_solution_attempt
                )

            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("stop", stop)
        ]
    )

    redis_host = REDIS_HOST
    redis_port = REDIS_PORT
    redis_password = REDIS_PASSWORD

    redis_connection = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        password=redis_password,
        decode_responses=True
    )
    questions = parce_questions(QUESTIONS_PATH)

    dispatcher.bot_data["redis_connection"] = redis_connection
    dispatcher.bot_data["questions_with_answers"] = questions
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
