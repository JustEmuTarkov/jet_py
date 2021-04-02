import tarkov
from tarkov.containers import Container
from tarkov.bots.container import BotContainer

if __name__ == "__main__":
    container = Container()
    container.wire(packages=[tarkov])

    bot_container = BotContainer()
    bot_container.wire(packages=[tarkov])

    import uvicorn  # type: ignore

    from server.app import app
    from server.certs import generate_ssl_certificate, is_ssl_certificate_expired

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
