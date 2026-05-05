import time
from typing import Optional, TypeVar

from spade.agent import BehaviourType

from common.models.base import ResponseBase
from common.models.common import ReqResAdapter

T = TypeVar("T", bound=ResponseBase)


async def wait_for_response(
    behav: BehaviourType, cls: type[T], timeout: float = 5
) -> Optional[T]:
    t0 = time.monotonic()
    t1 = t0 + timeout
    while True:
        t = time.monotonic()
        if t > t1:
            break
        reply = await behav.receive(timeout=max(0.1, t1 - t))

        try:
            if reply is None:
                return None
            res = ReqResAdapter.validate_json(reply.body)
            if isinstance(res, cls):
                return res
        except:
            continue
    return None
