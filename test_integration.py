import pytest
from fastapi.testclient import TestClient
from main import app
from models import CreateConversationRequest
import dependencies as deps
# constants
TEST_MONGO_OBJECT_ID_STR = "68a3818af78d37412183cd1e"
TEST_CHAT_ID = "c0ab6cba-65d8-412d-a940-9da77de5b85b"
TEST_EMAIL = "blaisdell.ryan11@gmail.com"
EXPECTED_MESSAGES = [
    {
        "role": "assistant",
        "content": "Hello! I'm your AI Code Reviewer. Paste your code below and I'll provide feedback.",
    },
    {
        "role": "user",
        "content": "Hi there!",
    }
]

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_retrieve_specific_existing_conversation_from_main_db(client: TestClient):
    """
    Verifies that a pre-existing conversation can be retrieved
    from the database.
    """
    # act
    response = client.get(
        "/chat",
        params={"chat_id": TEST_CHAT_ID, "email": TEST_EMAIL}
    )

    assert response.status_code == 200
    response_data = response.json()

    # assert verifying data
    assert response_data["_id"] == TEST_MONGO_OBJECT_ID_STR
    assert response_data["chat_id"] == TEST_CHAT_ID
    assert response_data["email"] == TEST_EMAIL

    # assert message length
    assert len(response_data["messages"]) == len(EXPECTED_MESSAGES)

    # assert message content
    for i, expected_msg in enumerate(EXPECTED_MESSAGES):
        actual_msg = response_data["messages"][i]
        assert actual_msg["role"] == expected_msg["role"]
        assert actual_msg["content"] == expected_msg["content"]

def test_create_new_conversation_in_database(client: TestClient):
    """
    Verifies that a conversation can be added into the database.
    """
    # arrange
    EXPECTED_CHAT_ID = "1234567"
    EXPECTED_EMAIL = "test@example.com"
    EXPECTED_SUCCESS_MESSAGE = "Conversation created successfully"

    # act
    response = client.post(
        "/create-chat",
        json={
            "chat_id": "1234567",
            "email": "test@example.com",
            "message": "How can I make a for loop in Java?"
        }
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data["chat_id"] == EXPECTED_CHAT_ID
    assert response_data["email"] == EXPECTED_EMAIL
    assert response_data["message"] == EXPECTED_SUCCESS_MESSAGE

    # cleanup (delete the test entry from DB)
    collection = deps.get_chat_collection()
    collection.delete_one({"chat_id": EXPECTED_CHAT_ID})