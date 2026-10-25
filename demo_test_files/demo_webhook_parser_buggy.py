"""
BRAND-NEW CUSTOM TEST FILE #2: Partner Webhook Deserialization Worker (CWE-502 Critical RCE)
"""
import pickle


def process_partner_settlement_packet(raw_packet: bytes, dynamic_rule: str):
    # CWE-502 CRITICAL: Arbitrary code execution via pickle.loads() + eval()
    packet_obj = pickle.loads(raw_packet)
    fee_override = eval(dynamic_rule)
    return {"packet": packet_obj, "fee": fee_override}
