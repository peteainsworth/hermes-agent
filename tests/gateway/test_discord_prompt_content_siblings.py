"""Sibling coverage for the embed-invisibility fix (send_exec_approval got it
in the same PR): slash confirm, clarify, and update prompts must also mirror
their payload into plain message content, since embeds don't render on some
Discord clients (web/mobile)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from gateway.config import PlatformConfig
from plugins.platforms.discord.adapter import DiscordAdapter


def _capture_channel(adapter):
    sent = {}

    async def fake_send(**kwargs):
        sent.update(kwargs)
        return SimpleNamespace(id=1234)

    channel = SimpleNamespace(send=AsyncMock(side_effect=fake_send))
    adapter._client = SimpleNamespace(
        get_channel=lambda _chat_id: channel,
        fetch_channel=AsyncMock(),
    )
    return sent


@pytest.mark.asyncio
async def test_slash_confirm_mirrors_message_into_content():
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="***"))
    sent = _capture_channel(adapter)

    result = await adapter.send_slash_confirm(
        chat_id="555",
        title="Reset session?",
        message="This will clear the current conversation history.",
        session_key="discord:555",
        confirm_id="c1",
    )

    assert result.success is True
    assert sent["view"] is not None
    assert sent["embed"] is not None
    assert "Reset session?" in sent["content"]
    assert "clear the current conversation history" in sent["content"]


@pytest.mark.asyncio
async def test_clarify_with_choices_mirrors_full_choices_into_content():
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="***"))
    sent = _capture_channel(adapter)
    long_choice = (
        "Option A (Recommended; select this when it best matches the requirements "
        "described in the question)"
    )

    result = await adapter.send_clarify(
        chat_id="555",
        question="Which option should be selected?",
        choices=[long_choice, "Option B (the alternative)"],
        clarify_id="cl1",
        session_key="discord:555",
    )

    assert result.success is True
    assert sent["view"] is not None
    assert "Which option should be selected?" in sent["content"]
    assert long_choice in sent["content"]
    assert "Option B (the alternative)" in sent["content"]
    assert sent["view"].children[0].label.endswith("…")


