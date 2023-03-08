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

