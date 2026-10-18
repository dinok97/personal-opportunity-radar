def get_last_ai_text(messages: list) -> str:
    for m in reversed(messages):
        if m.type != "ai" or getattr(m, "tool_calls", None):
            continue                                      
        content = m.content                             
        if isinstance(content, list):                     
            content = " ".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
        content = (content or "").strip()
        if content:
            return content
    return ""
