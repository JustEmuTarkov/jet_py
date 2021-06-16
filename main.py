import uvicorn

import tarkov
from server.app import app
from server.certs import generate_ssl_certificate, is_ssl_certificate_expired
from tarkov.bots.container import BotContainer
from tarkov.containers import ConfigContainer

if __name__ == "__main__":
    bot_container = BotContainer()
    bot_container.wire(packages=[tarkov])  # pylint: disable=no-member

    config_container = ConfigContainer()
    config_container.wire(packages=[tarkov])  # pylint: disable=no-member

    try:
        if is_ssl_certificate_expired():
            generate_ssl_certificate()
    except FileNotFoundError:
        generate_ssl_certificate()

    uvicorn.run(
        app,
        port=443,
        ssl_keyfile="certificates/private.key",
        ssl_certfile="certificates/cert.crt",
    )
