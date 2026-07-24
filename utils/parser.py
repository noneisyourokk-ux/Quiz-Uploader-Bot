import os
import json
from typing import List, Dict, Any


def clean_line(text: str) -> str:
    return text.strip().replace("\u200b", "")


def parse_txt_quiz(text: str) -> List[Dict[str, Any]]:
    """
    TXT format:

    Question?
    Option 1*
    Option 2
    Option 3
    Option 4
    Explanation: optional text

    Blank line separates questions.
    """
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    quizzes: List[Dict[str, Any]] = []

    for block in blocks:
        lines = [clean_line(x) for x in block.splitlines() if clean_line(x)]
        if len(lines) < 3:
            continue

        question = lines[0]
        explanation = ""
        options: List[str] = []
        correct_index = None

        for line in lines[1:]:
            if line.lower().startswith("explanation:"):
                explanation = line.split(":", 1)[1].strip()
                continue

            starred = line.endswith("*")
            option = line[:-1].strip() if starred else line.strip()

            if option:
                if starred:
                    correct_index = len(options)
                options.append(option)

        if len(options) < 2:
            continue

        if correct_index is None:
            correct_index = 0

        quizzes.append(
            {
                "question": question,
                "options": options,
                "correct": correct_index,
                "explanation": explanation,
            }
        )

    return quizzes


def parse_json_quiz(text: str) -> List[Dict[str, Any]]:
    """
    JSON format:

    [
      {
        "question": "Capital of India?",
        "options": ["Delhi", "Mumbai", "Kolkata", "Chennai"],
        "correct": 0,
        "explanation": "Delhi is the capital of India."
      }
    ]
    """
    data = json.loads(text)

    if not isinstance(data, list):
        raise ValueError("JSON must be a list of quiz objects")

    quizzes: List[Dict[str, Any]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        question = str(item.get("question", "")).strip()
        options = item.get("options", [])
        explanation = str(item.get("explanation", "")).strip()

        if not question or not isinstance(options, list):
            continue

        options = [str(x).strip() for x in options if str(x).strip()]
        if len(options) < 2:
            continue

        correct_index = 0

        if "correct" in item:
            c = item["correct"]
            if isinstance(c, int):
                correct_index = c
            elif isinstance(c, str):
                if c.isdigit():
                    correct_index = int(c)
                elif c in options:
                    correct_index = options.index(c)

        if "correct_text" in item:
            ct = str(item["correct_text"]).strip()
            if ct in options:
                correct_index = options.index(ct)

        if correct_index < 0 or correct_index >= len(options):
            correct_index = 0

        quizzes.append(
            {
                "question": question,
                "options": options,
                "correct": correct_index,
                "explanation": explanation,
            }
        )

    return quizzes


def parse_quiz_file(text: str, filename: str = "") -> List[Dict[str, Any]]:
    ext = os.path.splitext(filename.lower())[1]

    if ext == ".json":
        return parse_json_quiz(text)

    if ext == ".txt" or ext == "":
        stripped = text.lstrip()
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                return parse_json_quiz(text)
            except Exception:
                pass
        return parse_txt_quiz(text)

    try:
        return parse_json_quiz(text)
    except Exception:
        return parse_txt_quiz(text)
