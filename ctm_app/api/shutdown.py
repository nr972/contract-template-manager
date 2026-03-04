import asyncio
import os
import signal

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["shutdown"])


@router.post("/shutdown")
async def shutdown():
    """Send SIGTERM to the process after a short delay.

    The delay allows the HTTP 200 response to flush before the signal
    is delivered.  The startup script's trap handler cleans up all
    child processes.
    """

    async def _deferred_kill() -> None:
        await asyncio.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.get_running_loop().create_task(_deferred_kill())
    return {"status": "shutting_down"}
