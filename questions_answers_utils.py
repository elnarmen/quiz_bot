import re
from string import punctuation


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
    return leave_only_letters(user_answer.lower()) ==\
            leave_only_letters(matches.group().lower())