from pathlib import Path
from typing import Callable

import pytest
from dependency_injector.wiring import Provider, inject

import server.app
from server.container import AppContainer
from tarkov.profile.profile import Profile


@pytest.fixture(autouse=True, scope="session")
def app():
    return server.app


@pytest.fixture(scope="session")
def resources_path() -> Path:
    return Path("tests/resources").absolute()


@pytest.fixture(scope="session")
def profiles_path(resources_path) -> Path:
    return resources_path.joinpath("profiles")


@pytest.fixture(scope="function")
@inject
def profile(
    profiles_path,
    app,
) -> Profile:
    profile_provider = app.container.profile.profile.provider()
    profile = profile_provider(
        profile_id="9039420f851f50d547c06e93",
        profile_dir=profiles_path.joinpath("9039420f851f50d547c06e93"),
    )
    profile.read()
    return profile
