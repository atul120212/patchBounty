import asyncio
from decimal import Decimal
from cosmpy.aerial.client import LedgerClient, NetworkConfig
from uagents import Agent
from uagents.setup import fund_agent_if_low

ATESTFET_PER_FET = 10**18


class DoradoBountyLedger:
    """Real Fetch.ai Dorado Testnet wallet manager & on-chain bounty verifier for PatchBounty."""

    def __init__(self, coordinator: Agent, solvers: dict[str, Agent]) -> None:
        self.coordinator = coordinator
        self.solvers = solvers
        self.ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
        self.verified_tx_hashes: set[str] = set()
        self._lock = asyncio.Lock()

    def _query_fet_sync(self, fetch_addr: str) -> float:
        try:
            raw = self.ledger.query_bank_balance(fetch_addr, denom="atestfet")
            return round(float(Decimal(raw) / Decimal(ATESTFET_PER_FET)), 4)
        except Exception:
            return 0.0

    def _ensure_funded_sync(self) -> None:
        try:
            fund_agent_if_low(self.coordinator.wallet.address())
        except Exception:
            pass

    async def ensure_funded(self) -> dict:
        await asyncio.to_thread(self._ensure_funded_sync)
        return await self.get_wallets_snapshot()

    async def get_wallets_snapshot(self) -> dict:
        coord_addr = str(self.coordinator.wallet.address())
        coord_bal = await asyncio.to_thread(self._query_fet_sync, coord_addr)

        solver_entries = {}
        for key, ag in self.solvers.items():
            s_addr = str(ag.wallet.address())
            s_bal = await asyncio.to_thread(self._query_fet_sync, s_addr)
            solver_entries[key] = {
                "agent_key": key,
                "agent_name": ag.name,
                "address": s_addr,
                "balance_fet": s_bal,
                "explorer_url": f"https://companion.fetch.ai/dorado-1/accounts/{s_addr}",
            }

        return {
            "network": "Fetch.ai Dorado Testnet (dorado-1)",
            "denom": "TESTFET (atestfet)",
            "coordinator_wallet": {
                "label": "Maintainer Bounty Escrow Wallet",
                "address": coord_addr,
                "balance_fet": coord_bal,
                "explorer_url": f"https://companion.fetch.ai/dorado-1/accounts/{coord_addr}",
            },
            "solver_wallets": solver_entries,
        }

    def _broadcast_bounty_sync(self, recipient_addr: str, amount_fet: str) -> str:
        amount_raw = int(Decimal(amount_fet) * Decimal(ATESTFET_PER_FET))
        self._ensure_funded_sync()
        tx = self.ledger.send_tokens(
            recipient_addr,
            amount_raw,
            "atestfet",
            self.coordinator.wallet,
        )
        tx.wait_to_complete()
        return str(tx.tx_hash)

    def _verify_onchain_tx_sync(
        self, tx_hash: str, expected_recipient: str, min_amount_fet: str
    ) -> tuple[bool, dict | str]:
        clean = tx_hash.strip()
        if not clean or len(clean) < 40:
            return False, f"Invalid transaction hash format '{clean}' — rejected by Dorado ledger check."

        if clean.upper() in self.verified_tx_hashes:
            return False, f"Replay protection triggered: transaction {clean[:12]}... was already consumed."

        try:
            q = self.ledger.query_tx(clean)
        except Exception as exc:
            return False, f"Ledger query failed on Fetch Dorado: {exc}"

        if int(getattr(q, "code", 1)) != 0:
            return False, f"On-chain transaction failed with non-zero Cosmos code={q.code}."

        events = getattr(q, "events", {}) or {}
        transfer_ev = events.get("transfer", {})
        recipient = transfer_ev.get("recipient", "")
        amount_str = str(transfer_ev.get("amount", "0atestfet"))

        if recipient and recipient != expected_recipient:
            return False, f"Recipient mismatch: expected {expected_recipient}, got {recipient}."

        digits = "".join(ch for ch in amount_str if ch.isdigit())
        paid_raw = int(digits) if digits else 0
        min_raw = int(Decimal(min_amount_fet) * Decimal(ATESTFET_PER_FET))
        if paid_raw < min_raw:
            return False, f"Insufficient bounty transfer: paid {paid_raw} atestfet < required {min_raw}."

        self.verified_tx_hashes.add(clean.upper())
        height = int(getattr(q, "height", 0))
        return True, {
            "tx_hash": clean.upper(),
            "block_height": height,
            "recipient": expected_recipient,
            "paid_fet": str(Decimal(paid_raw) / Decimal(ATESTFET_PER_FET)),
            "explorer_url": f"https://companion.fetch.ai/dorado-1/transactions/{clean.upper()}",
        }

    async def broadcast_and_verify_bounty(
        self, recipient_addr: str, amount_fet: str, external_tx_hash: str | None = None
    ) -> tuple[bool, dict | str]:
        async with self._lock:
            tx_hash = external_tx_hash
            if not tx_hash:
                tx_hash = await asyncio.to_thread(
                    self._broadcast_bounty_sync, recipient_addr, amount_fet
                )
            return await asyncio.to_thread(
                self._verify_onchain_tx_sync, tx_hash, recipient_addr, amount_fet
            )
