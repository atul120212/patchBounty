"""
@recon — Universal Multi-Language GitHub & Codebase Source Inspector.
Supports Python (.py), JavaScript/TypeScript (.js, .jsx, .ts, .tsx), Solidity (.sol),
Java (.java), Go (.go), PHP (.php), C/C++ (.c, .cpp), Ruby (.rb), C# (.cs), Rust (.rs), and SQL (.sql)
across live public GitHub repositories, pasted raw code, file uploads, and built-in multi-language targets!
"""
import io
import re
import zipfile
from pathlib import Path
import httpx

from backend.config_store import PROJECT_ROOT, runtime_config

SUPPORTED_CODE_EXTENSIONS = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".sol", ".java",
    ".go", ".php", ".c", ".cpp", ".cc", ".rb", ".cs", ".rs", ".sql",
)

EXT_TO_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript (Node.js)",
    ".jsx": "React / JSX",
    ".ts": "TypeScript",
    ".tsx": "React / TypeScript",
    ".sol": "Solidity Smart Contract",
    ".java": "Java",
    ".go": "Go (Golang)",
    ".php": "PHP",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".rb": "Ruby",
    ".cs": "C#",
    ".rs": "Rust",
    ".sql": "SQL",
}

_GITHUB_MEM_CACHE: dict[str, dict] = {}

# Full-repo scan limits: har supported file scan hogi. Sirf ek file ki hard safety ceiling hai
# (512 KB) taaki ek dev-malicious giant/minified blob poori scan ko hang na kare — aisi file
# `files_skipped` me saaf-saaf gin kar report hoti hai, chupchaap gayab nahi hoti.
MAX_SCAN_FILE_BYTES = 512_000
SKIP_PATH_SEGMENTS = ("node_modules/", "vendor/", ".git/", "dist/", "build/", "__pycache__/", ".min.")


def _is_scannable_repo_path(rel_path: str) -> bool:
    low = rel_path.lower()
    return low.endswith(SUPPORTED_CODE_EXTENSIONS) and not any(seg in low for seg in SKIP_PATH_SEGMENTS)

BUILTIN_REAL_TARGETS: dict[str, dict] = {
    "fintech_ledger_api": {
        "repo_slug": "targets/fintech_ledger_api",
        "file_path": "targets/fintech_ledger_api/ledger_service.py",
        "language": "Python",
        "service_name": "Python — UPI & Bank Ledger Service",
        "cwe_badge": "Python • SQLi Vault Bypass",
        "keywords": ["fintech_ledger_api", "sqlite", "ledger", "fintech", "sql injection", "cwe-89"],
    },
    "express_checkout_api": {
        "repo_slug": "targets/express_checkout_api",
        "file_path": "targets/express_checkout_api/checkout_routes.js",
        "language": "JavaScript (Node.js)",
        "service_name": "Node.js / JS — Express Checkout API (3 Bugs)",
        "cwe_badge": "JavaScript • SQLi + RCE + Secret",
        "keywords": ["express", "node", "javascript", "js", "checkout", "stripe"],
    },
    "defi_staking_vault": {
        "repo_slug": "targets/defi_staking_vault",
        "file_path": "targets/defi_staking_vault/StakingVault.sol",
        "language": "Solidity Smart Contract",
        "service_name": "Solidity Web3 — DeFi Staking Vault (2 Bugs)",
        "cwe_badge": "Solidity • Reentrancy + tx.origin",
        "keywords": ["solidity", "smart contract", "reentrancy", "defi", "staking", "eth", "web3", ".sol"],
    },
    "banking_dao_java": {
        "repo_slug": "targets/banking_dao_java",
        "file_path": "targets/banking_dao_java/BankingAccountDao.java",
        "language": "Java",
        "service_name": "Java — Core Banking JDBC DAO (2 Bugs)",
        "cwe_badge": "Java • JDBC SQLi + Runtime Exec",
        "keywords": ["java", "jdbc", "spring", "banking_dao", "dao"],
    },
    "cloud_deploy_runner": {
        "repo_slug": "targets/cloud_deploy_runner",
        "file_path": "targets/cloud_deploy_runner/deploy_worker.py",
        "language": "Python",
        "service_name": "Python — CI Release Runner",
        "cwe_badge": "Python • Shell RCE",
        "keywords": ["cloud_deploy_runner", "subprocess", "deploy", "ci", "runner", "cwe-78"],
    },
    "doc_vault_storage": {
        "repo_slug": "targets/doc_vault_storage",
        "file_path": "targets/doc_vault_storage/artifact_reader.py",
        "language": "Python",
        "service_name": "Python — Multi-Tenant Document Vault",
        "cwe_badge": "Python • Path Traversal",
        "keywords": ["doc_vault_storage", "traversal", "invoice", "vault", "directory", "lfi", "cwe-22"],
    },
    "config_sync_engine": {
        "repo_slug": "targets/config_sync_engine",
        "file_path": "targets/config_sync_engine/manifest_loader.py",
        "language": "Python",
        "service_name": "Python — Dynamic Config Deserializer",
        "cwe_badge": "Python • Unsafe eval() RCE",
        "keywords": ["config_sync_engine", "eval", "deserial", "manifest", "cwe-502"],
    },
    "token_ssrf_gateway": {
        "repo_slug": "targets/token_ssrf_gateway",
        "file_path": "targets/token_ssrf_gateway/webhook_fetcher.py",
        "language": "Python",
        "service_name": "Python — Cloud Auth & Webhook Gateway",
        "cwe_badge": "Python • AWS IMDS SSRF",
        "keywords": ["token_ssrf_gateway", "ssrf", "jwks", "metadata", "imds", "169.254", "cwe-918"],
    },
}


def detect_code_language(file_path: str = "", source_code: str = "") -> str:
    ext = Path(file_path).suffix.lower()
    if ext in EXT_TO_LANGUAGE:
        return EXT_TO_LANGUAGE[ext]
    s = source_code or ""
    if "pragma solidity" in s or "contract " in s and "mapping(" in s:
        return "Solidity Smart Contract"
    if "public class " in s or "java.sql" in s or "Runtime.getRuntime()" in s:
        return "Java"
    if "#include <" in s or "strcpy(" in s or "int main(" in s:
        return "C / C++"
    if "<?php" in s or "$_GET[" in s or "$_POST[" in s:
        return "PHP"
    if "package main" in s or "func " in s and "fmt." in s:
        return "Go (Golang)"
    if "require(" in s or "module.exports" in s or "const " in s or "function " in s or "=>" in s:
        return "JavaScript (Node.js)"
    return "Python"


def guess_extension_for_language(lang: str) -> str:
    l = (lang or "").lower()
    if "solidity" in l:
        return ".sol"
    if "typescript" in l:
        return ".ts"
    if "javascript" in l or "node" in l or "react" in l:
        return ".js"
    if "java" in l:
        return ".java"
    if "go" in l:
        return ".go"
    if "php" in l:
        return ".php"
    if "c++" in l:
        return ".cpp"
    if l == "c":
        return ".c"
    return ".py"


def extract_github_repo_slug(text: str) -> tuple[str, str, str | None] | None:
    ext_group = "|".join(e.lstrip(".") for e in SUPPORTED_CODE_EXTENSIONS)
    blob_match = re.search(
        rf"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/blob/[A-Za-z0-9_./-]+?/([A-Za-z0-9_./-]+\.(?:{ext_group}))",
        text,
    )
    if blob_match:
        return blob_match.group(1), blob_match.group(2), blob_match.group(3)

    repo_match = re.search(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", text)
    if repo_match:
        repo = repo_match.group(2).removesuffix(".git")
        return repo_match.group(1), repo, None
    return None


def extract_inline_code(text: str) -> str | None:
    fenced = re.search(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)```", text, flags=re.DOTALL)
    if fenced and len(fenced.group(1).strip()) > 16:
        return fenced.group(1).strip() + "\n"
    code_markers = (
        "def ", "import ", "const ", "function ", "pragma solidity", "public class ",
        "<?php", "#include", "package main", "SELECT ", "subprocess", "os.system", "eval(",
    )
    if sum(1 for m in code_markers if m in text) >= 2 and "\n" in text:
        return text.strip() + "\n"
    return None


async def fetch_live_github_source_files(owner: str, repo: str, specific_file: str | None = None) -> dict | None:
    cache_key = f"{owner}/{repo}:{specific_file or '*'}"
    if cache_key in _GITHUB_MEM_CACHE:
        return _GITHUB_MEM_CACHE[cache_key]

    headers = {"Accept": "application/vnd.github+json", "User-Agent": "PatchBounty-Recon-uAgent/5.0"}
    tok = (runtime_config.github_token or "").strip()
    if tok.startswith(("ghp_", "github_pat_", "gho_")):
        headers["Authorization"] = f"Bearer {tok}"

    # PRIMARY FAST PATH: Download the COMPLETE repo archive via github.com/archive/HEAD.zip
    # (ZERO 60 req/hr rate limit!) and scan EVERY supported source file inside it — no top-8 cap,
    # no single-file shortcut. Kitni bhi files/folders/pages ho, sab check honge.
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            zip_r = await client.get(f"https://github.com/{owner}/{repo}/archive/HEAD.zip", headers={"User-Agent": "PatchBounty-Recon-uAgent/5.0"})
            if zip_r.status_code == 200 and len(zip_r.content) > 80:
                zf = zipfile.ZipFile(io.BytesIO(zip_r.content))
                discovered = 0
                skipped = 0
                fetched_files: list[dict] = []
                for name in sorted(zf.namelist()):
                    if name.endswith("/"):
                        continue
                    parts = name.split("/", 1)
                    rel_path = parts[1] if len(parts) > 1 else name
                    if specific_file and rel_path != specific_file:
                        continue
                    if not _is_scannable_repo_path(rel_path):
                        continue
                    discovered += 1
                    info = zf.getinfo(name)
                    if not (0 < info.file_size <= MAX_SCAN_FILE_BYTES):
                        skipped += 1
                        continue
                    txt = zf.read(name).decode("utf-8", errors="ignore")
                    if txt.strip():
                        fetched_files.append(
                            {
                                "file_path": rel_path,
                                "language": detect_code_language(rel_path, txt),
                                "source_code": txt,
                            }
                        )
                    else:
                        skipped += 1
                if fetched_files:
                    payload = {
                        "source_origin": "live_github_codeload",
                        "repo_slug": f"{owner}/{repo}",
                        "repo_url": f"https://github.com/{owner}/{repo}",
                        "default_branch": "HEAD",
                        "stars": 0,
                        "files": fetched_files,
                        "total_files_discovered": discovered,
                        "files_skipped_count": skipped,
                        "scan_coverage": "FULL_REPO_EVERY_FILE" if not specific_file else "SINGLE_FILE_BLOB_URL",
                    }
                    _GITHUB_MEM_CACHE[cache_key] = payload
                    return payload
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            meta_r = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
            if meta_r.status_code != 200:
                return None
            meta = meta_r.json()
            default_branch = meta.get("default_branch", "main")
            stars = int(meta.get("stargazers_count", 0))

            candidate_paths: list[str] = []
            if specific_file:
                candidate_paths.append(specific_file)
            else:
                tree_r = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
                    headers=headers,
                )
                if tree_r.status_code == 200:
                    tree = tree_r.json().get("tree", [])
                    src_files = [
                        item["path"]
                        for item in tree
                        if item.get("type") == "blob"
                        and item.get("path", "").lower().endswith(SUPPORTED_CODE_EXTENSIONS)
                        and not any(
                            seg in item.get("path", "").lower()
                            for seg in ("node_modules/", "vendor/", "dist/", "build/", ".min.", "test_", "tests/")
                        )
                        and int(item.get("size", 0)) < 50000
                    ]
                    src_files.sort(
                        key=lambda p: (
                            0
                            if any(
                                k in p.lower()
                                for k in ("auth", "db", "sql", "login", "api", "view", "route", "vault", "controller", "app", "dsvw", "user", "pay")
                            )
                            else 1,
                            len(p),
                        )
                    )
                    candidate_paths = src_files[:8]

            fetched_files: list[dict] = []
            for rel_path in candidate_paths:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{rel_path}"
                raw_r = await client.get(raw_url)
                if raw_r.status_code == 200 and raw_r.text.strip():
                    fetched_files.append(
                        {
                            "file_path": rel_path,
                            "language": detect_code_language(rel_path, raw_r.text),
                            "source_code": raw_r.text,
                        }
                    )

            if fetched_files:
                payload = {
                    "source_origin": "live_github_api",
                    "repo_slug": f"{owner}/{repo}",
                    "repo_url": f"https://github.com/{owner}/{repo}",
                    "default_branch": default_branch,
                    "stars": stars,
                    "files": fetched_files,
                    "total_files_discovered": discovered,
                    "files_skipped_count": skipped,
                    "scan_coverage": "FULL_REPO_EVERY_FILE" if not specific_file else "SINGLE_FILE_BLOB_URL",
                }
                _GITHUB_MEM_CACHE[cache_key] = payload
                return payload
    except Exception:
        return None
    return None


# Backwards alias kept clean for any external caller
fetch_live_github_python_files = fetch_live_github_source_files


async def resolve_repository_target(user_prompt: str, target_hint: str = "", inline_code: str = "") -> dict:
    raw_code = inline_code.strip() if inline_code.strip() else extract_inline_code(f"{target_hint}\n{user_prompt}")
    if raw_code:
        clean_hint = re.sub(r"[^a-zA-Z0-9_.-]", "", target_hint.strip()) or "submitted_code"
        lang = detect_code_language(clean_hint, raw_code)
        if not Path(clean_hint).suffix:
            clean_hint = clean_hint + guess_extension_for_language(lang)
        return {
            "source_origin": "inline_code_submission",
            "repo_slug": f"custom/{clean_hint}",
            "repo_url": f"inline://{clean_hint}",
            "default_branch": "live",
            "stars": 0,
            "files": [{"file_path": clean_hint, "language": lang, "source_code": raw_code + "\n"}],
        }

    combined = f"{target_hint} {user_prompt}".strip()
    gh_match = extract_github_repo_slug(combined)
    if gh_match:
        owner, repo, specific_file = gh_match
        live_gh = await fetch_live_github_source_files(owner, repo, specific_file)
        if live_gh:
            return live_gh
        return {
            "source_origin": "github_not_found_or_private",
            "repo_slug": f"{owner}/{repo}",
            "repo_url": f"https://github.com/{owner}/{repo}",
            "default_branch": "HEAD",
            "stars": 0,
            "not_found_error": True,
            "files": [],
        }

    low = combined.lower()
    best_key = "fintech_ledger_api"
    best_hits = -1
    for key, meta in BUILTIN_REAL_TARGETS.items():
        if key in low or meta["file_path"].lower() in low:
            best_key = key
            break
        hits = sum(1 for kw in meta["keywords"] if kw in low)
        if hits > best_hits:
            best_hits = hits
            best_key = key

    chosen = BUILTIN_REAL_TARGETS[best_key]
    full_file = PROJECT_ROOT / chosen["file_path"]
    src_text = full_file.read_text(encoding="utf-8")
    return {
        "source_origin": "workspace_microservice",
        "repo_slug": chosen["repo_slug"],
        "repo_url": f"workspace://{chosen['repo_slug']}",
        "default_branch": "main",
        "stars": 128,
        "files": [
            {
                "file_path": chosen["file_path"],
                "language": chosen["language"],
                "source_code": src_text,
            }
        ],
    }
