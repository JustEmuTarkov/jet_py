import uvicorn

from server_fastapi.app import app
from server_fastapi.certs import generate_ssl_certificate, is_ssl_certificate_expired

if __name__ == '__main__':
    try:
        if is_ssl_certificate_expired():
            generate_ssl_certificate()

    except FileNotFoundError:
        generate_ssl_certificate()
    uvicorn.run(
        app,
        ssl_keyfile='certificates/private.key',
        ssl_certfile='certificates/cert.crt'
    )
