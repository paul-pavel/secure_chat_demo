import argparse
from pathlib import Path
import ssl
import uvicorn
from app.main import create_app
from app.config import load_tls_config, TLSConfig


def ensure_self_signed(cert_path: Path, key_path: Path, cfg: TLSConfig):
    if cert_path.exists() and key_path.exists():
        return
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from datetime import datetime, timedelta

    key = rsa.generate_private_key(public_exponent=65537, key_size=cfg.key_bits)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, cfg.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, cfg.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, cfg.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, cfg.organization),
            x509.NameAttribute(NameOID.COMMON_NAME, cfg.common_name),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(minutes=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=cfg.valid_days))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(cfg.common_name)]), critical=False)
        .sign(key, hashes.SHA256())
    )
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def main():
    parser = argparse.ArgumentParser(description="Secure Chat Demo")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--tls", action="store_true", help="Enable HTTPS with TLS")
    parser.add_argument("--certfile", type=Path, default=Path("cert.pem"))
    parser.add_argument("--keyfile", type=Path, default=Path("key.pem"))
    parser.add_argument("--tls-config", type=Path, default=Path("tls_config.json"))
    args = parser.parse_args()

    app = create_app()

    ssl_ctx = None
    if args.tls:
        cfg = load_tls_config(args.tls_config)
        ensure_self_signed(args.certfile, args.keyfile, cfg)
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.load_cert_chain(certfile=str(args.certfile), keyfile=str(args.keyfile))

    uvicorn.run(app, host=args.host, port=args.port, ssl_keyfile=None if not ssl_ctx else str(args.keyfile), ssl_certfile=None if not ssl_ctx else str(args.certfile))


if __name__ == "__main__":
    main()
