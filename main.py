from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import anthropic
from anthropic.types import Message as AnthropicMessage
from dotenv import load_dotenv
from models import PromptRequest, PromptResponse, RegistrationRequest, RegistrationResponse
import logging as logger
from utilities import parse_claude_response
from pymongo import MongoClient
import os

### TODO

load_dotenv()
app = FastAPI()

try:
    client = anthropic.Anthropic()
    logger.info("Anthropic client initalized.")
except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}. Ensure ANTHROPIC_API_KEY is set in your .env file or environment.")

origins = [
    "http://localhost:3000"
    # add more urls after deploying or changing local host port
]

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

@app.post("/generate", response_model=PromptResponse)
async def generate_llm_response(request: PromptRequest):
    """  This POST endpoint will use the API Key to send a request to the Claude endpoint  """

    if not request.user_prompt:
        raise HTTPException(status_code=400, detail="User prompt cannot be empty")
    
    try:
        response: AnthropicMessage = client.messages.create(
            model = request.model,
            max_tokens = request.max_tokens,
            temperature = request.temperature, 
            messages = [
                {
                    "role": "user", 
                    "content": request.user_prompt
                }
            ],
            system = request.system_prompt
        ) # type: ignore

        claude_response: str = parse_claude_response(response)

        return PromptResponse(
            response = claude_response,
            model_used = response.model,
            tokens_generated = response.usage.output_tokens,
            input_tokens = response.usage.input_tokens
        )
    
    except Exception as e:
        logger.error(msg=f"Error has occured while generating the response: {e}")

        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")
    
@app.post("/register", response_model=RegistrationResponse)
async def register_user(request: RegistrationRequest):
    print("Received: ", request)

    if not request.email or not request.password:
          raise HTTPException(status_code=400, detail="Cannot create user with missing information.")

    mongo_client = MongoClient(os.getenv("MONGO_URI"))
    db = mongo_client["code_reviewer"]
    user_collection = db["users"]

    # Check if email already exists
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
