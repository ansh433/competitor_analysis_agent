import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import AbstractContextManager, asynccontextmanager
from functools import partial, wraps
from threading import Thread
from typing import TypeVar, cast

import fastapi.concurrency
import fastapi.dependencies.utils
import starlette.concurrency
import starlette.responses
from fastapi.routing import APIRoute

ReturnValue = TypeVar("ReturnValue")
IteratorValue = TypeVar("IteratorValue")
_end_of_iterator = object()


async def run_in_application_threadpool(
    callable_: Callable[..., ReturnValue],
    *args: object,
    **kwargs: object,
) -> ReturnValue:
    """Run blocking application work without relying on AnyIO's worker implementation."""

    call = partial(callable_, *args, **kwargs)
    result_box: list[ReturnValue] = []
    error_box: list[BaseException] = []

    def invoke() -> None:
        try:
            result_box.append(call())
        except BaseException as error:
            error_box.append(error)

    thread = Thread(target=invoke, name="competitor-api-call", daemon=True)
    thread.start()
    while thread.is_alive():
        await asyncio.sleep(0.002)
    thread.join()
    if error_box:
        raise error_box[0]
    return result_box[0]


async def iterate_in_application_threadpool(
    iterator: Iterator[IteratorValue],
) -> AsyncIterator[IteratorValue]:
    while True:
        item = await run_in_application_threadpool(_next_or_end, iterator)
        if item is _end_of_iterator:
            break
        yield cast(IteratorValue, item)


@asynccontextmanager
async def contextmanager_in_application_threadpool(
    context_manager: AbstractContextManager[IteratorValue],
) -> AsyncIterator[IteratorValue]:
    value = await run_in_application_threadpool(context_manager.__enter__)
    try:
        yield value
    except BaseException as error:
        suppress = await run_in_application_threadpool(
            context_manager.__exit__,
            type(error),
            error,
            error.__traceback__,
        )
        if not suppress:
            raise
    else:
        await run_in_application_threadpool(context_manager.__exit__, None, None, None)


def install_threadpool_compatibility() -> None:
    """Install the sync-route executor used by FastAPI and streaming responses."""

    fastapi.dependencies.utils.run_in_threadpool = run_in_application_threadpool
    fastapi.concurrency.run_in_threadpool = run_in_application_threadpool
    fastapi.concurrency.contextmanager_in_threadpool = contextmanager_in_application_threadpool
    fastapi.dependencies.utils.contextmanager_in_threadpool = (
        contextmanager_in_application_threadpool
    )
    starlette.concurrency.run_in_threadpool = run_in_application_threadpool
    starlette.concurrency.iterate_in_threadpool = iterate_in_application_threadpool
    starlette.responses.iterate_in_threadpool = iterate_in_application_threadpool


class ApplicationRoute(APIRoute):
    """Execute synchronous handlers before FastAPI builds response serialization policy."""

    def __init__(
        self,
        path: str,
        endpoint: Callable[..., object],
        **kwargs: object,
    ) -> None:
        if not asyncio.iscoroutinefunction(endpoint):
            synchronous_endpoint = endpoint

            @wraps(synchronous_endpoint)
            async def asynchronous_endpoint(*args: object, **values: object) -> object:
                return await run_in_application_threadpool(synchronous_endpoint, *args, **values)

            endpoint = asynchronous_endpoint
        super().__init__(path, endpoint, **kwargs)  # type: ignore[arg-type]


def _next_or_end(iterator: Iterator[IteratorValue]) -> IteratorValue | object:
    try:
        return next(iterator)
    except StopIteration:
        return _end_of_iterator
