import json
import openai
import os
from typing import Tuple

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")

def generate_summary_from_note(note_content: str) -> Tuple[str, str]:
    """
    Generates a concise and well-structured summary of a given note using OpenAI GPT,
    and detects the language of the input text.

    The summary preserves key information and may include structured elements like
    bullet points or tables if they enhance understanding. The summary will be returned
    in the same language as the input note.

    Args:
        note_content (str): The full text content of the note to be summarized.

    Returns:
        Tuple[str, str]: A tuple containing:
            - The generated summary (str)
            - The detected language of the note (str)
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that summarizes notes and identifies the language used. "
                        "When summarizing, create a clear and easy-to-understand summary. "
                        "If it helps comprehension, organize important information into tables, bullet points, or lists, "
                        "even if the original note doesn't explicitly use such formats."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Summarize the following note without missing important content, "
                        f"and tell me the language it is written in. "
                        f"Respond in JSON format like: {{\"summary\": \"...\", \"language\": \"...\"}}.\n"
                        f"Make sure the summary is written in the same language as the note.\n"
                        f"Note:\n{note_content}"
                    )
                }
            ],
            temperature=0.5,
            max_tokens=200
        )

        content = response['choices'][0]['message']['content'].strip()
        try:
            data = json.loads(content)
            summary = data.get("summary", "")
            language = data.get("language", "")
        except json.JSONDecodeError:
            summary = content
            language = ""
        return summary, language

    except Exception as error:
        print(f"OpenAI API error (summary): {error}")
        return "Summary could not be generated.", ""


def generate_flashcards_from_summary(ai_summary: str, language: str) -> list[dict]:
    """
    Creates 3–5 educational flashcards based on the given summary using OpenAI GPT.

    The function analyzes the structure of the summary (e.g. bullet points, tables, lists)
    to formulate meaningful questions that help reinforce understanding. Questions are designed
    not to reveal the answer directly. Responses are returned in the same language as the summary.

    Args:
        ai_summary (str): The summarized content from which flashcards will be generated.
        language (str): The language in which the flashcards should be written.

    Returns:
        list[dict]: A list of flashcard dictionaries with the keys:
            - "question" (str): The flashcard question.
            - "answer" (str): The flashcard answer.
    """
    try:
        prompt = (
            f"Based on the following summary, generate 3-5 educational flashcards. "
            f"Respond in the same language as the summary, which is {language}.\n\n"
            "Each flashcard should have a concise question and a clear, complete answer. "
            "Make sure the questions do NOT contain the answers. "
            "Use all structured content from the summary (tables, bullet points, lists) to create targeted questions. "
            "For example, if the summary contains a list of the 4 pillars of OOP, ask: "
            "'What are the 4 pillars of OOP?'\n\n"
            f"Summary:\n{ai_summary}"
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an educational assistant that creates clear flashcards "
                        "to help users learn efficiently."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        content = response['choices'][0]['message']['content']

        flashcards = []
        for block in content.strip().split("\n\n"):
            lines = block.strip().split("\n")
            if len(lines) == 2 and lines[0].startswith("Question:") and lines[1].startswith("Answer:"):
                flashcards.append({
                    "question": lines[0].replace("Question:", "").strip(),
                    "answer": lines[1].replace("Answer:", "").strip()
                })

        return flashcards
    except Exception as error:
        print(f"OpenAI API error (flashcards): {error}")
        return []

def check_user_answer_with_llm(question: str, correct_answer: str, user_answer: str, language: str) -> dict:
    """
    Evaluates a user's answer against the correct one using OpenAI GPT,
    and provides a short, constructive explanation.

    The evaluation identifies whether the answer is correct, incorrect, or partially correct.
    The feedback is phrased supportively and returned in the same language as the original content.

    Args:
        question (str): The original flashcard question.
        correct_answer (str): The correct answer as generated by the assistant.
        user_answer (str): The answer provided by the user.
        language (str): The language in which the evaluation should be returned.

    Returns:
        dict: A dictionary with a single key:
            - "evaluation" (str): The evaluation result and explanation.
    """
    try:
        prompt = (
            f"Question: {question}\n"
            f"Correct Answer: {correct_answer}\n"
            f"User's Answer: {user_answer}\n\n"
            "Evaluate the user's answer. Clearly state whether it is correct, incorrect, or partially correct. "
            "Provide a short, helpful explanation. "
            f"Your response must be written in {language}."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that checks user answers for accuracy and "
                        "provides a brief explanation. Always respond in the language of the question."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        result = response['choices'][0]['message']['content'].strip()
        return {"evaluation": result}
    except Exception as error:
        print(f"OpenAI API error (answer check): {error}")
        return {"evaluation": "Could not evaluate answer."}

