import json
import re

from typing import Tuple
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from src.config.config import Config

def get_openai_client():
    api_key = Config.OPENAI_API_KEY
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
                    "Return only JSON in the required format."
                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=(
                    "You will be given a user-written note. Your job is to:\n"
                    "1. Read and understand the note exactly as it is.\n"
                    "2. Detect its original language (e.g. en, de, fr, etc).\n"
                    "3. Write a **clear and concise summary** of the note that captures all key information.\n"
                    "4. Return your response in the following **exact JSON** format:\n\n"
                    "{ \"summary\": \"<summary here>\", \"language\": \"<language code>\" }\n\n"
                    "⚠️ Important:\n"
                    "- Do NOT add any explanations before or after the JSON.\n"
                    "- Do NOT mention originality or quality.\n"
                    "- Only return valid JSON.\n\n"
                    f"Note:\n{note_content}"
                )
            )
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()
        print("🔍 Raw summary response:\n", content)

        try:
            return_data = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    return_data = json.loads(match.group())
                except json.JSONDecodeError:
                    return_data = {}
            else:
                return_data = {}

        summary = return_data.get("summary", "").strip()
        language = return_data.get("language", "").strip()

        if not summary:
            summary = "Summary could not be extracted."
        return summary, language

    except Exception as error:
        print(f"❌ OpenAI API error (summary): {error}")
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
            "Format the output like this exactly:\n"
            "Question: ...\nAnswer: ...\n\n"
            "Do NOT use markdown or bullet points. Only plain text.\n\n"
            f"Summary:\n{ai_summary}"
        )

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content="You are an educational assistant that creates clear flashcards to help users learn efficiently."
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
        print("\n🔍 Raw flashcard output from OpenAI:\n", content)

        flashcards = []
        pattern = r"(?i)question[:\-–]\s*(.*?)\s*answer[:\-–]\s*(.*?)(?=\n{2,}|$)"
        matches = re.findall(pattern, content, re.DOTALL)

        for question, answer in matches:
            flashcards.append({
                "question": question.strip(),
                "answer": answer.strip()
            })

        print("✅ Parsed flashcards:", flashcards)
        return flashcards

    except Exception as error:
        print(f"❌ OpenAI API error (flashcards): {error}")
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
            "If the user's answer is just a repetition of the question or only an abbreviation without explanation, "
            "consider it incorrect and explain why. "
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
