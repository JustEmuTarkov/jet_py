from dependency_injector.wiring import Provide, inject
from fastapi.params import Depends

from server.container import AppContainer
from server.requests import ZLibRequest
from server.utils import make_router
from tarkov.dependencies import profile_manager
from tarkov.models import TarkovSuccessResponse
from tarkov.offraid.requests import OffraidSaveRequest
from tarkov.offraid.services import OffraidSaveService
from tarkov.profile.profile import Profile

offraid_router = make_router(tags=["Offraid"])


@offraid_router.put("/raid/profile/save")
@inject
def singleplayer_raid_profile_save(
    request: OffraidSaveRequest,
    profile: Profile = Depends(profile_manager.with_profile),
    offraid_service: OffraidSaveService = Depends(
        Provide[AppContainer.offraid.service]
    ),
) -> TarkovSuccessResponse:
    if request.is_player_scav:
        raise NotImplementedError

    offraid_service.update_profile(
        profile=profile,
        raid_profile=request.profile,
        raid_health=request.health,
    )

    return TarkovSuccessResponse(data=None)
