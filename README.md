# ai-code-reviewer
This is the FastAPI application that will be serving as the bridge between the UI and the Anthropic API.

The goal of this project is to make it easy for me to have a single location to use an LLM that knows how to respond to the code in the way I best see it.

The goal of the project is to give a central hub which can serve as a notetaking app, LLM chat, and a personal project.

## LLM Model
This project uses the Anthropic API to make calls.

In the future I want some sort of way to pick a model and use whichever one I believe would fit the task.

## Technologies being used
This current repo utilizes FastAPI to facilitate HTTP request, and the endpoints parse serve more request to the Anthropic API.

I plan on using some frontend framework with statemangement to persist the chats and notes while deploying it as a Dockerized container to AWS EC2 or something similar.

### Understanding the endpoint and Running the application
FastAPI is nice as it provides a built in OpenAPI spec that you can test through swagger.

1. Just clone the repo
2. Install deps with `pip install -r requirements.txt`
3. Start server with `uvicorn main:app --reload`
4. Visit `localhost:8000/docs` to see the endpoint

Anthropic API Key is required to test.

Just create a `.env ` file, and place the key in there as such `ANTHROPIC_API_KEY={your_key_here}`