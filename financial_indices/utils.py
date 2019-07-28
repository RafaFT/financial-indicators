import datetime
import functools
import logging
import os
import sys
import time
from typing import (Any,
                    Callable,
                    Optional,
                    )


logger = logging.getLogger(__name__)


# https://pyinstaller.readthedocs.io/en/v3.5/runtime-information.html
if getattr(sys, 'frozen', False):
    bundle_dir = os.getcwd()
else:
    bundle_dir = os.path.abspath(os.path.dirname(__file__))


def log_func_time(logger: logging.Logger, level: int = 20) -> Callable:
    """ Decorator to log the time it took to execute a given function.

    :param logger: Logger object to do logging.
    :param level: Level of logging (debug, info, etc) as integer.
    :param msg: Optional message that is appended to the time.
    :return: Function decorated.
    """

    log_map = {
        10: logger.debug,
        20: logger.info,
        30: logger.warning,
        40: logger.error,
        50: logger.critical,
    }

    try:
        log_writer = log_map[level]
    except KeyError:
        raise ValueError('Invalid level!')

    def time_function(function: Callable) -> Callable:

        @functools.wraps(function)
        def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()

            result = function(*args, **kwargs)

            end = time.perf_counter()

            message = f'{function.__name__}(*args, **kwargs) on {datetime.timedelta(seconds=round(end - start))}'

            log_writer(message)

            return result

        return wrapper

    return time_function


def singleton(class_: Callable) -> Callable:
    """ Decorator to implement singleton behavior to a given class.

    :param class_: Any class.
    :return: Decorated class.
    """

    @functools.wraps(class_)
    def wrapper(*args, **kwargs) -> Any:
        if wrapper._instance is None:
            wrapper._instance = class_(*args, **kwargs)

        return wrapper._instance

    wrapper._instance = None

    return wrapper


def create_log_path() -> Optional[str]:
    """ Defines the path to store logging. Attempts to create path if it does
    not exist.
    If successful, return path, else return None.

    :return: Path to log or None.
    """

    try:
        path = os.path.join(os.environ['USERPROFILE'], '.financial_indices')
    except KeyError:
        return None

    try:
        os.makedirs(path, exist_ok=True)
    except PermissionError:
        return None
    else:
        return path
