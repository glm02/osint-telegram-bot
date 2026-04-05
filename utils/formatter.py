def chunk_text(text: str, max_len: int = 4000) -> list[str]:
    """
    Découpe un texte long en blocs compatibles Telegram (max 4096 chars).
    """
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        chunks.append(text)
    return chunks
