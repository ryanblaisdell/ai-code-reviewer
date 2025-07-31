from anthropic.types import Message

def parse_claude_response(response: Message) -> str:
    claude_response = ""

    for response_block in response.content:
        if response_block.type == "text":
            claude_response += response_block.text

    return claude_response