from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import anthropic
from anthropic.types import Message as AnthropicMessage
from dotenv import load_dotenv
from models import PromptRequest, PromptResponse
import logging as logger
from utilities import parse_claude_response

### TODO

# make this serve the html pages or create some front end with another framework
# implement the endpoints that would retrieve the code from the user, possibly add input from the user as well to explain the code
# get the user input and send the payload to the LLM API
# ensure that the LLM has prompts being fed to it so that it will return a proper response
# update the UI with the response from the LLM API calls
# possibly add functionality to add a notes tab where the user can take notes from the feedback given
    # if this is the case, then research how easy it is to pertain state with no framework; some state management may be needed for development ease

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
        raise HTTPException(status_code=400, detail="User prompt cannot be empty!")
    
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