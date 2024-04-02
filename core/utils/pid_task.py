import functools
import os


__all__ = ['pid_task']


def pid_task(name=None):
    """
    Use that decorator only at target func to specify correct func name.

    :params: name - optional pid file name
    """
    from pidfile import AlreadyRunningError
    from pidfile import PIDFile

    from core.logger import Logger

    logger = Logger()

    if isinstance(name, type(None)):
        name = ''
    else:
        name = f"-{name}"

    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args):
            pid_file = os.path.join(
                os.getcwd(),
                '.pids', f"{os.getppid()}{name}-{func.__name__}.pid"
            )
            if not os.path.exists(pid_dir := os.path.dirname(pid_file)):
                os.makedirs(pid_dir)
            try:
                with PIDFile(pid_file):
                    return await func(*args)
            except AlreadyRunningError:
                pass
            except (KeyboardInterrupt, OSError):
                try:
                    os.remove(pid_file)
                except Exception:
                    pass
            except Exception as e:
                logger.exception(
                    f"Task [{func.__name__}] exception:\n{e}"
                )

        return wrapped

    return wrapper
