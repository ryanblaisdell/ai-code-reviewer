from contextlib import asynccontextmanager
import time
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import anthropic
from anthropic.types import (Message as AnthropicMessage, ToolChoiceAutoParam, MessageParam)
from dotenv import load_dotenv
from models import PromptRequest, PromptResponse, RegistrationRequest, RegistrationResponse, ConversationResponse, ConversationRequest, CreateConversationRequest, GenerateChatTitleInput, GENERATE_CHAT_TITLE_TOOL_SPEC
import logging as logger
from utilities import parse_claude_response
from pymongo import MongoClient
from pymongo.collection import Collection as MongoCollection
import dependencies as deps
import os
from typing import Any, Dict, Iterable, List, Optional, cast

load_dotenv()

try:
    client = anthropic.Anthropic()
    logger.info("Anthropic client initalized.")
except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}. Ensure ANTHROPIC_API_KEY is set in your .env file or environment.")

origins = [
    "http://localhost:3000"
    # add more urls after deploying or changing local host port
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI environment variable not set.")

        deps.mongo_client_instance = MongoClient(mongo_uri)
        db = deps.mongo_client_instance["code_reviewer"]

        deps.chat_collection_instance = db["chats"]
        deps.users_collection_instance = db["users"]

        print("Connected to MongoDB and initialized collections successfully!")

    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database startup failed: {str(e)}")

    yield

    print("Shutting down...")
    if deps.mongo_client_instance:
        deps.mongo_client_instance.close()
        print("MongoDB connection closed.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,       
    allow_methods=["*"],          
    allow_headers=["*"],          
)
        
@app.get("/")
def root():
    return { "message" : "Welcome to the AI Code Reviewer!" }

#region LLM API Endpoint

@app.post("/generate", response_model=PromptResponse)
async def generate_llm_response(
    request: PromptRequest,
    chats_db_collection: MongoCollection = Depends(deps.get_chat_collection)
):
    """
    This POST endpoint will use the API Key to send a request to the Claude endpoint
    and return a message responding to the user.
    """

    if not request.user_prompt or not request.chat_id:
        raise HTTPException(status_code=400, detail="User prompt or ChatID cannot be empty")
    
    chat_doc = chats_db_collection.find_one({"chat_id": request.chat_id})
    
    if not chat_doc:
        raise HTTPException(status_code=404, detail=f"Chat with ID {request.chat_id} not found.")

    existing_messages_from_db: List[Dict[str, Any]] = chat_doc.get("messages", [])

    llm_message_history: list[MessageParam] = []

    for msg in existing_messages_from_db:
        role = msg.get("role")
        content = msg.get("content")
        if role == "user" and isinstance(content, str):
            llm_message_history.append(cast(MessageParam, {"role": "user", "content": content}))
        elif role == "assistant" and isinstance(content, str):
            llm_message_history.append(cast(MessageParam, {"role": "assistant", "content": content}))
        
    llm_message_history.append(cast(MessageParam, {"role": "user", "content": request.user_prompt}))
    
    try:
        response: AnthropicMessage = client.messages.create(
            model = request.model,
            max_tokens = request.max_tokens,
            temperature = request.temperature, 
            messages = llm_message_history,
            system = request.system_prompt
        )

        claude_response: str = parse_claude_response(response)

        input_tokens = response.usage.input_tokens
        tokens_generated = response.usage.output_tokens

        timestamp = time.time()
        
        messages_to_push = [
            {"role": "user", "content": request.user_prompt, "timestamp": timestamp},
            {"role": "assistant", "content": claude_response.strip(), "timestamp": timestamp}
        ]

        chats_db_collection.update_one(
            {"chat_id": request.chat_id},
            {
                "$push": {"messages": {"$each": messages_to_push}},
                "$set": {"updated_at": timestamp}, 
                "$inc": {
                    "total_input_tokens": input_tokens,
                    "total_output_tokens": tokens_generated
                }
            }
        )

        return PromptResponse(
            response = claude_response,
            chat_id = request.chat_id,
            model_used = request.model,
            tokens_generated = tokens_generated,
            input_tokens = input_tokens,
            message = "LLM response generated and chat updated successfully."
        )

    except Exception as e:
        logger.error(msg=f"Error has occured while generating the response: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")
    
#endregion

#region Registration Endpoints

@app.post("/register", response_model=RegistrationResponse)
async def register_user(request: RegistrationRequest, users_db_collection=Depends(deps.get_users_collection)):

    if not request.email or not request.password:
          raise HTTPException(status_code=400, detail="Cannot create user with missing information.")

    mongo_client = MongoClient(os.getenv("MONGO_URI"))
    db = mongo_client["code_reviewer"]
    user_collection = db["users"]

    existing_user = user_collection.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    try:
        result = user_collection.insert_one({
            "name": request.name,
            "email": request.email,
            "password": request.password
        })

        return RegistrationResponse(
            id=str(result.inserted_id),
            name=request.name,
            email=request.email
        )
    
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

#endregion

#region Conversation Endpoints

@app.get("/chats", response_model=List[ConversationResponse])
async def retrieve_all_conversations(
    email: str,
    chats_db_collection: MongoCollection = Depends(deps.get_chat_collection) 
):
    if not email:
        raise HTTPException(
            status_code=400, 
            detail="Cannot find conversation with missing information. Please provide email..."
        )
    
    try:
        db_results = chats_db_collection.find({ "email": email })
        results = list(db_results)

        if results is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No conversations found for user.")
        
        conversations = []
        for doc in results:
            doc["_id"] = str(doc["_id"])
            conversations.append(ConversationResponse(**doc))

        return conversations

    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")
    
@app.get("/chat", response_model=ConversationResponse)
async def retrieve_conversation(
    request: ConversationRequest = Depends(), 
    chats_db_collection: MongoCollection = Depends(deps.get_chat_collection)
):
     
    if not request.chat_id or not request.email:
        raise HTTPException(
            status_code=400, 
            detail="Cannot find conversation with missing information."
        )
    
    try:
        result = chats_db_collection.find_one({
            "email": request.email,
            "chat_id": request.chat_id
        })

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        
        result["_id"] = str(result["_id"])
        
        return ConversationResponse(**result)
    
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")
    
@app.post("/create-chat")
async def create_conversation(
    request: CreateConversationRequest, 
    chats_db_collection: MongoCollection = Depends(deps.get_chat_collection)
):

    if not request.chat_id or not request.email or not request.message:
        raise HTTPException(
            status_code=400, 
            detail="Cannot create conversation with missing information. Check that all information is provided."
        )
    
    tool_instruction = (
        "Based on the following user request, you must perform a task in your response: "
        "1. **Call the `generate_chat_title` tool.** The `conversation_summary` field in the tool input "
        "   should contain a concise and relevant title for this conversation. "
        "\n\n"
    )
    
    messages_payload: Iterable[MessageParam] = [
        {
            "role": "user",
            "content": (
                f"User request: {request.message}\n\n"
                f"{tool_instruction}"
            )
        }
    ]

    tools_to_use = [GENERATE_CHAT_TITLE_TOOL_SPEC]
    tool_choice_setting: ToolChoiceAutoParam = {"type": "auto"}
    
    try:
        timestamp = time.time()

        title_response: AnthropicMessage = client.messages.create(
                model = request.model,
                max_tokens = 1000,
                temperature = request.temperature,
                messages = messages_payload,
                system = request.system_prompt,
                tools = tools_to_use,
                tool_choice = tool_choice_setting
            )
        
        generated_title: Optional[str] = None

        for content_block in title_response.content:
            if content_block.type == 'tool_use':
                try:
                    title_input = GenerateChatTitleInput.model_validate(content_block.input)
                    generated_title = title_input.conversation_summary.strip()

                except Exception as tool_error:
                    logger.error(f"Error parsing generate_chat_title tool input: {tool_error}")
                    generated_title = None
            else:
                logger.warning(f"Claude used an unexpected tool.")

        print("Generate Chat: ", generated_title)

        message_response: AnthropicMessage = client.messages.create(
            model = request.model,
            max_tokens = 4000,
            temperature = request.temperature,
            messages = [{
                "role": "user",
                "content": request.message
            }],
            system = request.system_prompt
        )

        claude_response: str = parse_claude_response(message_response)

        doc = {
            "chat_id": request.chat_id,
            "email": request.email,
            "messages": [
                {
                    "role": "user",
                    "content": request.message,
                    "timestamp": timestamp
                },
                {
                    "role": "assistant",
                    "content": claude_response.strip(),
                    "timestamp": timestamp

                }
            ],
            "created_at": timestamp,
            "updated_at": timestamp,
            "title": generated_title
        }

        result = chats_db_collection.insert_one(doc)

        return {
            "chat_id": request.chat_id,
            "insert_id": str(result.inserted_id),
            "email": request.email,
            "response": claude_response.strip(),
            "title": generated_title,
            "message": "Conversation created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

#endregion
