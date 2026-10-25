"""
Real vulnerable microservice module #4: Dynamic Pricing Rule Evaluator.
Contains genuine CWE-502 / CWE-95 Unsafe Code Execution via `eval()` on untrusted config JSON/dict strings.
"""


def parse_partner_fee_config(raw_payload: str) -> dict:
    # VULNERABLE SINK (CWE-502): Unsafe eval() allows arbitrary Python expression execution
    parsed = eval(raw_payload)
    if not isinstance(parsed, dict):
        raise ValueError("Configuration payload must evaluate to a dictionary")
    return parsed
