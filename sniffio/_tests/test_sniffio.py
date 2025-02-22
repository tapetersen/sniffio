import os
import sys

import pytest

from .. import (
    current_async_library, AsyncLibraryNotFoundError,
    current_async_library_cvar, thread_local
)


def test_basics_cvar():
    with pytest.raises(AsyncLibraryNotFoundError):
        current_async_library()

    token = current_async_library_cvar.set("generic-lib")
    try:
        assert current_async_library() == "generic-lib"
    finally:
        current_async_library_cvar.reset(token)

    with pytest.raises(AsyncLibraryNotFoundError):
        current_async_library()


def test_basics_tlocal():
    with pytest.raises(AsyncLibraryNotFoundError):
        current_async_library()

    old_name, thread_local.name = thread_local.name, "generic-lib"
    try:
        assert current_async_library() == "generic-lib"
    finally:
        thread_local.name = old_name

    with pytest.raises(AsyncLibraryNotFoundError):
        current_async_library()


def test_asyncio():
    import asyncio

    with pytest.raises(AsyncLibraryNotFoundError):
        current_async_library()

    ran = []

    async def this_is_asyncio():
        assert current_async_library() == "asyncio"
        # Call it a second time to exercise the caching logic
        assert current_async_library() == "asyncio"
        ran.append(True)

    asyncio.run(this_is_asyncio())
    assert ran == [True]

    with pytest.raises(AsyncLibraryNotFoundError):
        current_async_library()


def test_in_call_soon_threadsafe():
    import asyncio

    asynclib = None

    def sync_in_loop(completed):
        nonlocal asynclib
        try:
            asynclib = current_async_library()
        finally:
            completed.set()

    async def async_in_loop():
        completed = asyncio.Event()
        loop.call_soon_threadsafe(sync_in_loop, completed)
        await completed.wait()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(async_in_loop())
    loop.close()

    assert asynclib == 'asyncio'


# https://github.com/dabeaz/curio/pull/354
@pytest.mark.skipif(
    os.name == "nt" and sys.version_info >= (3, 9),
    reason="Curio breaks on Python 3.9+ on Windows. Fix was not released yet",
)
def test_curio():
    import curio

    with pytest.raises(AsyncLibraryNotFoundError):
        current_async_library()

    ran = []

    async def this_is_curio():
        assert current_async_library() == "curio"
        # Call it a second time to exercise the caching logic
        assert current_async_library() == "curio"
        ran.append(True)

    curio.run(this_is_curio)
    assert ran == [True]

    with pytest.raises(AsyncLibraryNotFoundError):
        current_async_library()
