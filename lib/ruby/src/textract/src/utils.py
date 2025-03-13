# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import asyncio
import random
from typing import Any, Callable, Dict

from loguru import logger

DEFAULT_MAX_RETRIES = 10
DEFAULT_BASE_DELAY = 2.0
DEFAULT_MAX_DELAY = 30.0


def _exponential_backoff(*, attempt: int, base_delay: float = 2.0, max_delay: float = 30.0) -> float:
    """Calculate exponential backoff delay with jitter."""
    return min(max_delay, (base_delay**attempt) + (random.random()))


async def retry_operation(
    func: Callable,
    *args: Any,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    max_retries: int = DEFAULT_MAX_RETRIES,
    **kwargs: Any,
) -> Any:
    """Execute a function with retries."""
    logger.debug(f"Starting retry operation for {func.__name__}")
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"All retry attempts failed for {func.__name__}")
                raise e
            delay = _exponential_backoff(attempt=attempt, base_delay=base_delay, max_delay=max_delay)
            logger.debug(f"Retry attempt {attempt + 1} for {func.__name__}, waiting {delay:.2f} seconds")
            await asyncio.sleep(delay)


async def get_paginated_results(
    *,
    client: Any,
    method: str,
    initial_params: Dict[str, Any],
    result_key: str,
) -> Dict[str, Any]:
    """Handle pagination for AWS API results."""
    logger.debug(f"Starting pagination for {method} with key {result_key}")
    complete_result = None
    next_token = None
    method_to_call = getattr(client, method)

    while True:
        params = initial_params.copy()
        if next_token:
            params["NextToken"] = next_token

        response = await retry_operation(method_to_call, **params)

        if complete_result is None:
            complete_result = response
        else:
            complete_result[result_key].extend(response[result_key])

        next_token = response.get("NextToken")
        if not next_token:
            break

    return complete_result
