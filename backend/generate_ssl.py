from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pathlib import Path
import datetime
import argparse
import ipaddress

LOCAL_DIR = Path(__file__).parent / ".local"
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

KEY_PATH = LOCAL_DIR / "key.pem"
CERT_PATH = LOCAL_DIR / "cert.pem"

def _split_hosts(values: list[str] | None) -> list[str]:
    if not values:
        return []

    hosts: list[str] = []
    for value in values:
        for part in value.split(","):
            normalized = part.strip()
            if normalized:
                hosts.append(normalized)
    return hosts


def _subject_alt_names(hosts: list[str]) -> list[x509.GeneralName]:
    names: list[x509.GeneralName] = []
    for host in hosts:
        try:
            names.append(x509.IPAddress(ipaddress.ip_address(host)))
        except ValueError:
            names.append(x509.DNSName(host))
    return names


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a self-signed SSL certificate.")
    parser.add_argument(
        "--host",
        dest="hosts",
        action="append",
        help="DNS name or IP address to include in the certificate. May be passed multiple times or comma-separated.",
    )
    return parser.parse_args()


def generate_self_signed_cert(hosts: list[str] | None = None):
    normalized_hosts = _split_hosts(hosts) or ["localhost", "127.0.0.1"]
    common_name = normalized_hosts[0]

    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Berlin"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Berlin"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Customer Manager"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.UTC)
    ).not_valid_after(
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName(_subject_alt_names(normalized_hosts)),
        critical=False,
    ).sign(key, hashes.SHA256())
    
    # Save private key
    with open(KEY_PATH, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    
    # Save certificate
    with open(CERT_PATH, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"SSL certificate generated successfully!")
    print(f"Key: {KEY_PATH}")
    print(f"Certificate: {CERT_PATH}")
    print(f"Hosts: {', '.join(normalized_hosts)}")

if __name__ == "__main__":
    args = _parse_args()
    generate_self_signed_cert(args.hosts)