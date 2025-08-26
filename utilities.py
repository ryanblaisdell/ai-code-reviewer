from anthropic.types import Message as AnthropicMessage

def parse_claude_response(response: AnthropicMessage) -> str:
    text_content = []
    for content_block in response.content:
        if content_block.type == 'text':
            text_content.append(content_block.text)
    return "".join(text_content)