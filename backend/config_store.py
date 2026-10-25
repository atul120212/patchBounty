"""
Centralized Runtime Configuration & True 50/50 Dual ASI:One Load Balancer (`asi1` + `asi1-mini`).
Alternates strictly 50/50 across Fetch.ai's flagship `asi1` reasoning model and ultra-fast `asi1-mini`
model on a single `ASI_ONE_API_KEY`, with automatic 45s cooldown failover and zero HTTP 429 crashes.
"""
import hashlib
import os
import threading
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH, override=False)

SIBLING_ENV = PROJECT_ROOT.parent / "project-1-dealsetu" / ".env"
if SIBLING_ENV.exists():
    load_dotenv(SIBLING_ENV, override=False)


class RuntimeConfig:
    def __init__(self) -> None:
        self.asi_one_api_key: str = os.getenv("ASI_ONE_API_KEY", "").strip()
        self.asi_one_base_url: str = os.getenv("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1").strip()
        self.flagship_model: str = os.getenv("ASI_ONE_FLAGSHIP_MODEL", "asi1").strip()
        self.fast_model: str = os.getenv("ASI_ONE_FAST_MODEL", "asi1-mini").strip()
        self.routing_mode: str = os.getenv("ASI_ONE_ROUTING_MODE", "dual_round_robin").strip()
        self.seed_salt: str = os.getenv("AEGIS_SEED_SALT", "patchbounty-aegis-v3-2026").strip()
        self.dorado_buyer_seed: str = os.getenv("PATCHBOUNTY_MAINTAINER_SEED", os.getenv("DORADO_BUYER_SEED", "")).strip()
        self.dorado_researcher_seed: str = os.getenv("PATCHBOUNTY_RESEARCHER_SEED", os.getenv("DORADO_SELLER_SEED", "")).strip()
        self.github_token: str = os.getenv("GITHUB_TOKEN", "").strip()
        self.agentverse_api_key: str = os.getenv("AGENTVERSE_API_KEY", "").strip()

        # SMTP Email Delivery Credentials (for sending automated resolution reports)
        self.smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user: str = os.getenv("SMTP_USER", "").strip()
        self.smtp_pass: str = os.getenv("SMTP_PASS", "").strip()
        self.smtp_from: str = os.getenv("SMTP_FROM", "").strip()

        self._llm_sem = threading.BoundedSemaphore(2)
        self._rr_lock = threading.Lock()
        self._rr_turn: int = 0
        self._model_cooldown_until: dict[str, float] = {}
        self._response_cache: dict[str, tuple[float, str, str]] = {}
        self.total_live_calls: int = 0
        self.model_usage_counts: dict[str, int] = {"asi1": 0, "asi1-mini": 0, "deterministic-guard": 0}

    def update_credentials(
        self,
        asi_one_api_key: str | None = None,
        github_token: str | None = None,
        agentverse_api_key: str | None = None,
        dorado_buyer_seed: str | None = None,
        routing_mode: str | None = None,
        smtp_host: str | None = None,
        smtp_port: int | str | None = None,
        smtp_user: str | None = None,
        smtp_pass: str | None = None,
        smtp_from: str | None = None,
    ) -> dict:
        updates_to_persist: dict[str, str] = {}
        if asi_one_api_key is not None and asi_one_api_key.strip():
            self.asi_one_api_key = asi_one_api_key.strip()
            updates_to_persist["ASI_ONE_API_KEY"] = self.asi_one_api_key
        if github_token is not None and github_token.strip():
            self.github_token = github_token.strip()
            updates_to_persist["GITHUB_TOKEN"] = self.github_token
        if agentverse_api_key is not None and agentverse_api_key.strip():
            self.agentverse_api_key = agentverse_api_key.strip()
            updates_to_persist["AGENTVERSE_API_KEY"] = self.agentverse_api_key
        if dorado_buyer_seed is not None and dorado_buyer_seed.strip():
            self.dorado_buyer_seed = dorado_buyer_seed.strip()
            updates_to_persist["DORADO_BUYER_SEED"] = self.dorado_buyer_seed
        if routing_mode is not None and routing_mode.strip():
            self.routing_mode = routing_mode.strip()
            updates_to_persist["ASI_ONE_ROUTING_MODE"] = self.routing_mode

        if smtp_host is not None:
            self.smtp_host = smtp_host.strip()
            updates_to_persist["SMTP_HOST"] = self.smtp_host
            os.environ["SMTP_HOST"] = self.smtp_host
        if smtp_port is not None and str(smtp_port).strip():
            try:
                self.smtp_port = int(str(smtp_port).strip())
                updates_to_persist["SMTP_PORT"] = str(self.smtp_port)
                os.environ["SMTP_PORT"] = str(self.smtp_port)
            except ValueError:
                pass
        if smtp_user is not None:
            self.smtp_user = smtp_user.strip()
            updates_to_persist["SMTP_USER"] = self.smtp_user
            os.environ["SMTP_USER"] = self.smtp_user
        if smtp_pass is not None:
            self.smtp_pass = smtp_pass.strip()
            updates_to_persist["SMTP_PASS"] = self.smtp_pass
            os.environ["SMTP_PASS"] = self.smtp_pass
        if smtp_from is not None:
            self.smtp_from = smtp_from.strip()
            updates_to_persist["SMTP_FROM"] = self.smtp_from
            os.environ["SMTP_FROM"] = self.smtp_from

        if updates_to_persist:
            self._response_cache.clear()
            existing: dict[str, str] = {}
            if ENV_PATH.exists():
                for line in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        existing[k.strip()] = v.strip()
            existing.update(updates_to_persist)
            ENV_PATH.write_text(
                "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n",
                encoding="utf-8",
            )
        return self.public_status()

    def reload_from_disk(self) -> None:
        for p in (SIBLING_ENV, ENV_PATH):
            if p.exists():
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k == "ASI_ONE_API_KEY" and v:
                            self.asi_one_api_key = v
                        elif k == "GITHUB_TOKEN" and v:
                            self.github_token = v
                        elif k == "AGENTVERSE_API_KEY" and v:
                            self.agentverse_api_key = v
                        elif k in ("DORADO_BUYER_SEED", "PATCHBOUNTY_MAINTAINER_SEED") and v:
                            self.dorado_buyer_seed = v
                        elif k == "SMTP_HOST" and v:
                            self.smtp_host = v
                            os.environ["SMTP_HOST"] = v
                        elif k == "SMTP_PORT" and v:
                            try:
                                self.smtp_port = int(v)
                                os.environ["SMTP_PORT"] = v
                            except ValueError:
                                pass
                        elif k == "SMTP_USER" and v:
                            self.smtp_user = v
                            os.environ["SMTP_USER"] = v
                        elif k == "SMTP_PASS" and v:
                            self.smtp_pass = v
                            os.environ["SMTP_PASS"] = v
                        elif k == "SMTP_FROM" and v:
                            self.smtp_from = v
                            os.environ["SMTP_FROM"] = v

    def public_status(self) -> dict:
        masked_key = ""
        if len(self.asi_one_api_key) >= 10:
            masked_key = f"{self.asi_one_api_key[:5]}...{self.asi_one_api_key[-4:]}"
        masked_gh = f"{self.github_token[:4]}...{self.github_token[-4:]}" if len(self.github_token) >= 8 else ""
        masked_av = f"{self.agentverse_api_key[:5]}...{self.agentverse_api_key[-4:]}" if len(self.agentverse_api_key) >= 9 else ""
        masked_smtp_user = ""
        if "@" in self.smtp_user:
            u, domain = self.smtp_user.split("@", 1)
            masked_smtp_user = f"{u[:2]}***@{domain}"
        elif self.smtp_user:
            masked_smtp_user = f"{self.smtp_user[:2]}***"

        return {
            "asi_one_configured": bool(self.asi_one_api_key),
            "asi_one_masked": masked_key,
            "github_token_masked": masked_gh,
            "agentverse_key_masked": masked_av,
            "dorado_seed_configured": bool(self.dorado_buyer_seed),
            "flagship_model": self.flagship_model,
            "fast_model": self.fast_model,
            "routing_mode": self.routing_mode,
            "github_token_configured": bool(self.github_token),
            "agentverse_configured": bool(self.agentverse_api_key),
            "total_live_calls": self.total_live_calls,
            "model_usage_counts": dict(self.model_usage_counts),
            "smtp_configured": bool(self.smtp_host and self.smtp_user and self.smtp_pass),
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_user_masked": masked_smtp_user,
            "smtp_from": self.smtp_from or self.smtp_user or "security@patchbounty.agent",
        }

    def _pick_model_order(self, prefer_flagship: bool) -> list[str]:
        if self.routing_mode == "flagship_only":
            return [self.flagship_model, self.fast_model]
        if self.routing_mode == "fast_only":
            return [self.fast_model, self.flagship_model]
        with self._rr_lock:
            idx = self._rr_turn
            self._rr_turn += 1
        if idx % 2 == 0:
            return [self.flagship_model, self.fast_model]
        return [self.fast_model, self.flagship_model]

    async def complete_asi_one(
        self,
        messages: list[dict],
        prefer_flagship: bool = True,
        max_tokens: int = 550,
        temperature: float = 0.25,
        timeout: float = 14.0,
    ) -> tuple[str | None, str]:
        if not self.asi_one_api_key:
            self.reload_from_disk()
        if not self.asi_one_api_key:
            self.model_usage_counts["deterministic-guard"] += 1
            return None, "no-api-key"

        cache_digest = hashlib.sha256(
            f"{max_tokens}:{repr(messages)}".encode("utf-8", errors="ignore")
        ).hexdigest()
        now = time.monotonic()
        cached = self._response_cache.get(cache_digest)
        if cached and (now - cached[0]) < 180.0:
            return cached[1], cached[2]

        order = self._pick_model_order(prefer_flagship)
        available_models = [m for m in order if self._model_cooldown_until.get(m, 0.0) <= now]
        if not available_models:
            available_models = order

        self._llm_sem.acquire()
        try:
            client = AsyncOpenAI(
                api_key=self.asi_one_api_key,
                base_url=self.asi_one_base_url,
                max_retries=0,
            )
            for mdl in available_models:
                try:
                    resp = await client.chat.completions.create(
                        model=mdl,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=timeout,
                    )
                    content = (resp.choices[0].message.content or "").strip()
                    if content:
                        self.total_live_calls += 1
                        self.model_usage_counts[mdl] = self.model_usage_counts.get(mdl, 0) + 1
                        if len(self._response_cache) > 128:
                            self._response_cache.clear()
                        self._response_cache[cache_digest] = (time.monotonic(), content, mdl)
                        return content, mdl
                except Exception as exc:
                    err_s = str(exc).lower()
                    if "429" in err_s or "rate" in err_s or "too many" in err_s:
                        self._model_cooldown_until[mdl] = time.monotonic() + 45.0
                    continue
        finally:
            self._llm_sem.release()
        self.model_usage_counts["deterministic-guard"] += 1
        return None, "asi1-fallback"


runtime_config = RuntimeConfig()
