from src.data.models import Flashcard

def test_full_workflow(login_auth_client, session, create_user):
    long_content = (
        "Artificial intelligence (AI) is intelligence demonstrated by machines, "
        "unlike the natural intelligence displayed by humans and animals. "
        "Leading AI textbooks define the field as the study of 'intelligent agents': "
        "any device that perceives its environment and takes actions that maximize "
        "its chance of successfully achieving its goals. AI applications include "
        "advanced web search engines, recommendation systems, understanding human speech, "
        "self-driving cars, automated decision-making, and competing at the highest level "
        "in strategic game systems. Despite the progress, AI faces challenges including "
        "ensuring ethical use, addressing bias in data, and creating systems that can "
        "reason and understand context deeply. The future of AI depends heavily on "
        "ongoing research and the integration of AI into diverse domains."
    )

    response = login_auth_client.post('/note/store-note', json={
        "title": "Artificial Intelligence Overview",
        "content": long_content
    })
    assert response.status_code == 201
    note_id = response.get_json()["note_id"]

    resp_summary = login_auth_client.post(f"/llm/generate-summary/{note_id}")
    assert resp_summary.status_code == 200

    session.commit()
    session.expire_all()

    resp_flashcards = login_auth_client.post(f"/llm/generate-flashcard/{note_id}")
    assert resp_flashcards.status_code == 201

    session.commit()
    session.expire_all()

    resp_quiz = login_auth_client.post(f"/quiz/start/{note_id}")
    assert resp_quiz.status_code == 200

    flashcards = resp_quiz.get_json().get("flashcards")
    assert flashcards and len(flashcards) > 0

    max_cards = 10
    for fc in flashcards[:max_cards]:
        card_id = fc["card_id"]
        flashcard_obj = session.query(Flashcard).filter_by(card_id=card_id).first()
        assert flashcard_obj is not None

        question = flashcard_obj.question
        correct_answer = flashcard_obj.answer
        language = flashcard_obj.note.language if flashcard_obj.note else "en"
        user_answer = "This is my dummy test answer"

        resp_check = login_auth_client.post("/llm/check-answer", json={
            "question": question,
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "language": language
        })
        assert resp_check.status_code == 200

        feedback = resp_check.get_json()
        assert "evaluation" in feedback

        session.refresh(flashcard_obj)

        assert flashcard_obj.learned is False

        print("----- Flashcard -----")
        print(f"Question: {question}")
        print(f"Answer: {correct_answer}")
        print(f"Feedback: {feedback['evaluation']}")
        print("---------------------\n")
