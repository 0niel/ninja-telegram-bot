import time
from multiprocessing import Pool, Process
from typing import Any, Mapping, Union

from bot.utils.safe_exec.secure_compiler import secure_compile


class ExecProcessException(Exception):
    """
    Raised when an exception occurs in a task subprocess.
    """


class ExecTimeoutError(Exception):
    """
    Raised when the execution times out.
    """


class Executor:
    def __init__(
        self,
        timeout: Union[int, float] = 15,
        checks_per_second: int = 40,
    ):
        self.timeout = timeout
        self.check_interval = 1 / checks_per_second

    def execute(
        self,
        code: str,
        custom_globals: dict[str, Any],
        custom_locals: Mapping[str, object],
    ) -> float:
        """
        Safely executes Python code.
        """
        task = SubprocessTask(self, code, custom_globals, custom_locals)

        code = secure_compile(code, "<string>", "exec")

        task.run()
        limit = time.time() + self.timeout

        while time.time() < limit:
            time.sleep(self.check_interval)
            if not task.is_running():
                exec_time = time.time() - task.exec_start
                return exec_time

        task.stop()
        # raise ExecTimeoutError("Timed out!")


class SubprocessTask:
    def __init__(
        self,
        executor: Executor,
        code: str,
        custom_globals: dict[str, Any],
        custom_locals: Mapping[str, object],
    ):
        self.executor = executor
        self.code = code
        self._globals = custom_globals
        self._locals = custom_locals

    def _start_exec(self, code, _globals, _locals):
        try:
            exec(code, _globals, _locals)
        except Exception as msg:
            try:
                _globals.get("__builtins__").get("print")(str(msg))
            except TypeError:
                pass

    def run(self):
        """
        Runs the task in subprocess.
        """
        self.exec_start = time.time()
        self.process = Process(
            target=self._start_exec,
            args=(self.code, self._globals, self._locals),
        )
        self.process.start()
        self.pid = self.process.pid

    def is_running(self) -> bool:
        """
        Checks if the task is still running.
        """
        return self.process.is_alive()

    def stop(self):
        """
        Kill the subprocess.
        """
        self.process.terminate()
