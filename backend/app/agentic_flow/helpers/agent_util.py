
def get_last_ai_text(messages: list) -> str:
    for m in reversed(messages):
        if m.type != "ai" or getattr(m, "tool_calls", None):
            continue                                    
        
        content = (content or "").strip()

        if content:
            return content
    
    return ""