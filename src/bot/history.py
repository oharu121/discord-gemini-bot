"""Conversation history management for Discord bot."""

import discord


async def get_conversation_history(
    channel: discord.TextChannel | discord.DMChannel | discord.Thread,
    bot_id: int,
    limit: int = 10
) -> list[dict[str, str | list[str]]]:
    """
    Fetch recent messages where bot was involved (sliding window strategy).

    Args:
        channel: The Discord channel to fetch history from
        bot_id: The bot's user ID
        limit: Maximum number of bot-involved messages to return

    Returns:
        List of message dicts in Gemini format: {"role": "user"|"model", "parts": [content]}
    """
    history: list[dict[str, str | list[str]]] = []

    # Scan last 50 messages to find bot-involved ones
    async for msg in channel.history(limit=50):
        # Skip empty messages
        if not msg.content:
            continue

        # Include if: bot sent it, or bot was mentioned
        is_bot_message = msg.author.id == bot_id
        is_bot_mentioned = bot_id in [u.id for u in msg.mentions]

        if is_bot_message or is_bot_mentioned:
            # Clean content: remove bot mention for user messages
            content = msg.content
            if is_bot_mentioned and not is_bot_message:
                content = content.replace(f"<@{bot_id}>", "").strip()

            history.append({
                "role": "model" if is_bot_message else "user",
                "parts": [content]
            })

            if len(history) >= limit:
                break

    # Reverse to chronological order (oldest first)
    return list(reversed(history))
