import os
import json

from typing import Tuple
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)

def generate_summary_from_note(note_content: str) -> Tuple[str, str]:
    """
    Generates a concise summary of a note and detects the language using OpenAI's GPT models.

    The summary maintains essential content and may use structured formatting like bullet points or tables.
    The language of the input is automatically detected, and the summary is returned in that language.

    Args:
        note_content (str): The full text of the note to summarize.

    Returns:
        Tuple[str, str]: A tuple containing:
            - The generated summary (str)
            - The detected language of the note (str)
    """
    client = get_openai_client()
    try:
        messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are an assistant that summarizes notes and identifies the language used. "
                    "When summarizing, create a clear and easy-to-understand summary. "
                    "If it helps comprehension, organize important information into tables, bullet points, or lists, "
                    "even if the original note doesn't explicitly use such formats."
                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=(
                    f"Summarize the following note without missing important content, "
                    f"and tell me the language it is written in. "
                    f"Respond in JSON format like: {{\"summary\": \"...\", \"language\": \"...\"}}.\n"
                    f"Make sure the summary is written in the same language as the note.\n"
                    f"Note:\n{note_content}"
                )
            )
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,
            max_tokens=200
        )

        content = response.choices[0].message.content.strip()

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
    Generates 3–5 educational flashcards from a given summary using OpenAI's GPT models.

    The assistant identifies structured content (e.g. lists, tables) to formulate meaningful flashcard questions
    and answers. Questions are designed to not contain the answers directly. All output is returned in the specified language.

    Args:
        ai_summary (str): The summary content to base flashcards on.
        language (str): The language in which the flashcards should be written.

    Returns:
        list[dict]: A list of flashcard dictionaries, each containing:
            - "question" (str): The flashcard question.
            - "answer" (str): The flashcard answer.
    """
    client = get_openai_client()
    try:
        prompt = (
            f"Based on the following summary, generate 3–5 educational flashcards. "
            f"Respond in the same language as the summary, which is {language}.\n\n"
            "Each flashcard should have a concise question and a clear, complete answer. "
            "Make sure the questions do NOT contain the answers. "
            "Use all structured content from the summary (tables, bullet points, lists) to create targeted questions. "
            "For example, if the summary contains a list of the 4 pillars of OOP, ask: "
            "'What are the 4 pillars of OOP?'\n\n"
            f"Summary:\n{ai_summary}"
        )

        messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are an educational assistant that creates clear flashcards "
                    "to help users learn efficiently."
                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=prompt
            )
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()

        flashcards = []
        for block in content.split("\n\n"):
            lines = block.strip().split("\n")
            if len(lines) == 2 and lines[0].startswith("Question:") and lines[1].startswith(
                    "Answer:"):
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
    Evaluates the user's answer against the correct answer using OpenAI's GPT models,
    and returns a brief explanation in the specified language.

    The assistant determines whether the answer is correct, incorrect, or partially correct,
    and provides constructive feedback to help the user understand their mistake or success.

    Args:
        question (str): The original flashcard question.
        correct_answer (str): The expected correct answer.
        user_answer (str): The answer provided by the user.
        language (str): The language to use in the feedback.

    Returns:
        dict: A dictionary containing:
            - "evaluation" (str): The assistant's evaluation and explanation.
    """
    client = get_openai_client()
    try:
        prompt = (
            f"Question: {question}\n"
            f"Correct Answer: {correct_answer}\n"
            f"User's Answer: {user_answer}\n\n"
            "Evaluate the user's answer. Clearly state whether it is correct, incorrect, or partially correct. "
            "Provide a short, helpful explanation. "
            f"Your response must be written in {language}."
        )

        messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=(
                    "You are an assistant that checks user answers for accuracy and "
                    "provides a brief explanation. Always respond in the language of the question."
                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=prompt
            )
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=150
        )

        result = response.choices[0].message.content.strip()
        return {"evaluation": result}

    except Exception as error:
        print(f"OpenAI API error (answer check): {error}")
        return {"evaluation": "Could not evaluate answer."}

