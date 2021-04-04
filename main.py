import tarkov
from tarkov.containers import ConfigContainer, Container, RepositoriesContainer
from tarkov.bots.container import BotContainer
from tarkov.fleamarket.containers import FleaMarketContainer

if __name__ == "__main__":
    import uvicorn  # type: ignore

    from server.app import app
    from server.certs import generate_ssl_certificate, is_ssl_certificate_expired

    container = Container()
    container.wire(packages=[tarkov])

    repositories_container = RepositoriesContainer()
    repositories_container.wire(packages=[tarkov])

    bot_container = BotContainer()
    bot_container.wire(packages=[tarkov])

    flea_container = FleaMarketContainer()
    flea_container.wire(packages=[tarkov])

    config_container = ConfigContainer()
    config_container.wire(packages=[tarkov])

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
