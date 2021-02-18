import datetime
import random
from pathlib import Path

from OpenSSL import crypto  # type: ignore


def is_ssl_certificate_expired() -> bool:
    with Path("certificates/cert.crt").open("rb") as file:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, file.read())
        return cert.has_expired()


def generate_ssl_certificate() -> None:
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)
    x509 = crypto.X509()
    subject = x509.get_subject()
    subject.C = "Ru"
    subject.ST = "Tarkov"
    subject.L = "Ru"
    subject.O = "Jet"  # noqa: E741
    subject.OU = "Jet"
    subject.CN = "Jet"
    x509.set_serial_number(random.randint(1, 2 ** 20 - 1))

    datetime_format = "%Y%m%d%H%M%SZ"

    not_before = datetime.datetime.now() + datetime.timedelta(days=-1)
    x509.set_notBefore(not_before.strftime(datetime_format).encode())

    expiration_date = datetime.datetime.now() + datetime.timedelta(days=365 * 42)
    x509.set_notAfter(expiration_date.strftime(datetime_format).encode())

    x509.set_issuer(x509.get_subject())
    x509.set_pubkey(pkey)

    x509.sign(pkey, "sha512")

    Path("certificates").mkdir(exist_ok=True)
    with Path("certificates/cert.crt").open("w") as file:
        file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, x509).decode("utf8"))

    with Path("certificates/private.key").open("w") as file:
        file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey).decode("utf8"))
