"""
Unit Test Suite for Subagents Calling in Master Agent Chat & Coordinated Swarm Execution.
Tests:
  1. Swarm Roster & 6-uAgent registration.
  2. Subagent overview commands via Master Chat ("status of subagents", "list agents", etc.).
  3. Individual subagent targeted queries (@recon, @specter, @forge, @warden, @vault).
  4. End-to-end multi-agent security audit coordination in Master Chat.
  5. Clean code scan subagent coordination (0 bugs, $0 bounty, no payment request).
  6. Direct SwarmCoordinationTask message handlers across all 5 subagents.
"""
import asyncio
from unittest.mock import MagicMock
from uuid import uuid4

from uagents_core.contrib.protocols.chat import ChatMessage, TextContent
from uagents_core.contrib.protocols.payment import RequestPayment

from backend.asi_one_agent import (
    aegis,
    forge,
    get_swarm_roster,
    handle_asi_one_chat,
    recon,
    route_subagent_command,
    specter,
    vault,
    warden,
    recon_handle_task,
    specter_handle_task,
    forge_handle_task,
    warden_handle_task,
    vault_handle_task,
    SwarmCoordinationTask,
    SwarmCoordinationResult,
)


class MockContext:
    def __init__(self):
        self.sent_messages = []
        self.logger = MagicMock()

    async def send(self, recipient: str, message):
        self.sent_messages.append((recipient, message))


def test_01_swarm_subagents_roster():
    roster = get_swarm_roster()
    assert len(roster) == 6
    handles = [ag["handle"] for ag in roster]
    assert "@aegis" in handles
    assert "@recon" in handles
    assert "@specter" in handles
    assert "@forge" in handles
    assert "@warden" in handles
    assert "@vault" in handles


def test_02_route_subagent_overview_queries():
    async def _test():
        test_queries = [
            "status of subagents",
            "show me subagents",
            "who are the subagents?",
            "list agents in swarm",
            "ping swarm",
            "active agents",
        ]
        for q in test_queries:
            matched, reply = await route_subagent_command(q)
            assert matched is True, f"Failed to match subagent query: {q}"
            assert "@recon" in reply
            assert "@specter" in reply
            assert "@forge" in reply
            assert "@warden" in reply
            assert "@vault" in reply

    asyncio.run(_test())


def test_03_route_individual_subagents_queries():
    async def _test():
        # @recon
        m, r = await route_subagent_command("@recon status and capabilities")
        assert m is True
        assert "@recon" in r
        assert "GitHub Hunter" in r
        assert "Comment-Safe" in r

        # @specter
        m, r = await route_subagent_command("@specter prove")
        assert m is True
        assert "@specter" in r
        assert "Red-Team" in r
        assert "SHA-256" in r

        # @forge
        m, r = await route_subagent_command("@forge patch strategies")
        assert m is True
        assert "@forge" in r
        assert "@blade" in r
        assert "@kestrel" in r
        assert "@titan" in r

        # @warden
        m, r = await route_subagent_command("@warden sandbox gate")
        assert m is True
        assert "@warden" in r
        assert "Dual Duel" in r

        # @vault
        m, r = await route_subagent_command("@vault escrow balance")
        assert m is True
        assert "@vault" in r
        assert "Dorado Testnet" in r
        assert "TESTFET" in r

    asyncio.run(_test())


def test_04_master_chat_subagents_query_invocation():
    async def _test():
        ctx = MockContext()
        msg = ChatMessage(
            msg_id=uuid4(),
            content=[TextContent(type="text", text="Status of subagents")],
        )
        await handle_asi_one_chat(ctx, "user-test-sender", msg)

        # Must send ChatAcknowledgement first, then ChatMessage with swarm breakdown
        assert len(ctx.sent_messages) >= 2
        chat_replies = [m for _, m in ctx.sent_messages if isinstance(m, ChatMessage)]
        assert len(chat_replies) == 1
        reply_text = chat_replies[0].content[0].text
        assert "@aegis" in reply_text
        assert "@recon" in reply_text
        assert "@specter" in reply_text
        assert "@forge" in reply_text
        assert "@warden" in reply_text
        assert "@vault" in reply_text

    asyncio.run(_test())


def test_05_master_chat_vulnerable_target_calling_subagents():
    async def _test():
        ctx = MockContext()
        msg = ChatMessage(
            msg_id=uuid4(),
            content=[TextContent(type="text", text="Audit express_checkout_api microservice")],
        )
        await handle_asi_one_chat(ctx, "user-test-sender", msg)

        chat_replies = [m for _, m in ctx.sent_messages if isinstance(m, ChatMessage)]
        payment_requests = [m for _, m in ctx.sent_messages if isinstance(m, RequestPayment)]

        assert len(chat_replies) == 1
        reply_text = chat_replies[0].content[0].text

        # Verifies all 5 subagents are credited with their coordinated actions
        assert "@recon" in reply_text
        assert "@specter" in reply_text
        assert "@forge" in reply_text
        assert "@warden" in reply_text
        assert "@vault" in reply_text

        # Verifies payment request on Dorado testnet
        assert len(payment_requests) == 1
        pr = payment_requests[0]
        assert pr.accepted_funds[0].amount == "0.05"
        assert pr.accepted_funds[0].currency == "FET"
        assert pr.metadata.get("chain_id") == "dorado-1"

    asyncio.run(_test())


def test_06_master_chat_clean_code_scan_subagents():
    async def _test():
        ctx = MockContext()
        msg = ChatMessage(
            msg_id=uuid4(),
            content=[TextContent(type="text", text="https://github.com/jonschlinkert/is-odd")],
        )
        await handle_asi_one_chat(ctx, "user-test-sender", msg)

        chat_replies = [m for _, m in ctx.sent_messages if isinstance(m, ChatMessage)]
        payment_requests = [m for _, m in ctx.sent_messages if isinstance(m, RequestPayment)]

        assert len(chat_replies) == 1
        reply_text = chat_replies[0].content[0].text

        assert "0 Vulnerabilities" in reply_text
        assert "@recon" in reply_text
        assert "@vault" in reply_text
        assert "$0 Bounty" in reply_text
        assert len(payment_requests) == 0, "Clean code must never issue a payment request!"

    asyncio.run(_test())


def test_07_subagent_coordination_task_messages():
    async def _test():
        subagents = [
            ("@recon", recon_handle_task),
            ("@specter", specter_handle_task),
            ("@forge", forge_handle_task),
            ("@warden", warden_handle_task),
            ("@vault", vault_handle_task),
        ]
        for handle, handler_fn in subagents:
            ctx = MockContext()
            task = SwarmCoordinationTask(task_id="ping-test", action="PING")
            await handler_fn(ctx, aegis.address, task)
            assert len(ctx.sent_messages) == 1
            recipient, res = ctx.sent_messages[0]
            assert recipient == aegis.address
            assert isinstance(res, SwarmCoordinationResult)
            assert res.agent_handle == handle
            assert res.status == "OK"

    asyncio.run(_test())
