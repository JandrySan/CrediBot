def build_ai_history(message_repository, conversation_id: int, limit: int = 8) -> list[dict]:
    rows = message_repository.get_recent_messages(
        conversation_id=conversation_id,
        limit=limit,
    )
    return [
        {
            "role": "assistant" if row.direction == "OUTBOUND" else "user",
            "content": row.content.strip(),
        }
        for row in reversed(rows)
        if (row.content or "").strip()
    ]
