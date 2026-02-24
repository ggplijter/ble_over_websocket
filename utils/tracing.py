import logging

import time

logger = logging.getLogger(__name__)
class EnterExitLog:
    def __init__(self, funcName):
        self.funcName = funcName

    def __enter__(self):
        logger.info(f"Started: {self.funcName}")
        self.init_time = time.time()
        return self

    def __exit__(self, type, value, tb):
        logger.info(
            f"Finished: {self.funcName} in: {(time.time() - self.init_time)*1000:.2f} msec"
        )


def func_logger_decorator(func):
    def func_wrapper(*args, **kwargs):
        with EnterExitLog(func.__name__):
            return func(*args, **kwargs)

    return func_wrapper
