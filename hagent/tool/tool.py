# See LICENSE for details

from typing import Optional
import os
import shutil
import subprocess
from abc import abstractmethod

from hagent.core.tracer import TracerABCMetaClass


class Tool(metaclass=TracerABCMetaClass):
    """
    Base class for all HAgent tools.

    This class provides common functionality and a standard interface
    for all HAgent tools, including error handling, setup validation,
    and common utility methods.
    """

    def __init__(self):
        """Initialize the base tool with default values."""
        self.error_message = ''
        self._is_ready = False

    def set_error(self, message: str) -> None:
        """
        Set an error message and mark the tool as not ready.

        Args:
            message: The error message to store
        """
        self.error_message = message
        self._is_ready = False

    def is_ready(self) -> bool:
        """
        Check if the tool is ready for use.

        Returns:
            True if the tool is set up and ready, False otherwise.
        """
        return self._is_ready

    def get_error(self) -> str:
        """
        Get the current error message.

        Returns:
            The error message string.
        """
        return self.error_message

    @abstractmethod
    def setup(self, *args, **kwargs) -> bool:
        """
        Setup the tool with the given parameters.

        This method must be implemented by subclasses.

        Returns:
            True if setup was successful, False otherwise.
        """
        pass

    def check_executable(self, executable: str, path: Optional[str] = None) -> bool:
        """
        Check if an executable exists and is accessible.

        Args:
            executable: The name of the executable to check
            path: Optional specific path to check, if None uses system PATH

        Returns:
            True if the executable is found and accessible, False otherwise.
        """
        if path:
            exec_path = os.path.join(path, executable)
            if not (os.path.exists(exec_path) and os.access(exec_path, os.X_OK)):
                self.set_error(f'{executable} not found or not executable at {exec_path}')
                return False
            return True
        else:
            which_result = shutil.which(executable)
            if not which_result:
                self.set_error(f'{executable} not found in PATH')
                return False
            return True

    def run_command(self, cmd, cwd=None, timeout=60, capture_output=True, check=False, text=True):
        """
        Run a command and handle exceptions in a standardized way.

        Args:
            cmd: Command to run (list or string)
            cwd: Working directory for the command
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise an exception on non-zero exit
            text: Whether to return strings (vs bytes)

        Returns:
            A CompletedProcess object from subprocess.run()

        Raises:
            Sets error_message and returns None on failure
        """
        try:
            return subprocess.run(cmd, cwd=cwd, timeout=timeout, capture_output=capture_output, check=check, text=text)
        except subprocess.TimeoutExpired as e:
            self.set_error(f'Command timed out after {timeout}s: {e}')
            return None
        except subprocess.CalledProcessError as e:
            self.set_error(f'Command failed with return code {e.returncode}: {e}')
            return None
        except Exception as e:
            self.set_error(f'Error running command: {e}')
            return None
