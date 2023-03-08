import logging
import os
from random import choice
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CallbackContext, CommandHandler
from telegram.ext import MessageHandler, Filters, ConversationHandler

from config import TG_TOKEN, QUESTIONS_PATH
from service_functions import parce_questions, check_user_answer, connect_db


logger = logging.getLogger(__name__)

USER_CHOICE = range(1)


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

    return USER_CHOICE


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

    redis_connection = connect_db()
    questions_with_answers = parce_questions(QUESTIONS_PATH)

    dispatcher.bot_data["redis_connection"] = redis_connection
    dispatcher.bot_data["questions_with_answers"] = questions_with_answers
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
