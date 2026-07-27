def charge_count(retry_tokens: list[str]) -> int:
    """Return how many charge attempts the current checkout submits."""
    return len(retry_tokens)
