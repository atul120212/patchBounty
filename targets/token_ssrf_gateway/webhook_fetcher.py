"""
Microservice Target #5: Token & Webhook Metadata Gateway (`CWE-918` Server-Side Request Forgery).
Unpatched implementation passes untrusted `jwks_endpoint_url` straight into an internal metadata resolver
without blocking cloud link-local IMDSv1 (`169.254.169.254`) or loopback addresses.
"""
import urllib.parse

MOCK_CLOUD_IMDS = {
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/prod-role": (
        '{"AccessKeyId":"AKIA_PROD_VAULT_KEY_77","SecretAccessKey":"wJalrXUtnFEMI_LIVE_ROOT_SECRET"}'
    ),
    "https://auth.partner-bank.example/jwks.json": '{"keys":[{"kid":"bank-rsa-01","kty":"RSA"}]}',
}


def fetch_partner_jwks(jwks_endpoint_url: str) -> str:
    # VULNERABLE SINK (CWE-918): Unvalidated URL scheme/host fetches cloud IMDS credentials!
    parsed = urllib.parse.urlparse(jwks_endpoint_url)
    if not parsed.scheme:
        raise ValueError("Missing URL scheme")
    return MOCK_CLOUD_IMDS.get(jwks_endpoint_url, '{"keys":[]}')
