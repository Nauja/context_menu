from __future__ import annotations
from typing import TYPE_CHECKING
import inspect
import os
import platform

if TYPE_CHECKING:
    from typing import Tuple
    from types import FunctionType

    MethodInfo = Tuple[str, str, str]

PLATFORM_WINDOWS = "Windows"
PLATFORM_LINUX = "Linux"


def get_method_info(python: FunctionType) -> MethodInfo:
    """Gets information about a function.

    :return: a tuple (function name, function file name, path to function directory)
    """
    func_file_path = os.path.abspath(inspect.getfile(python))

    func_dir_path = os.path.dirname(func_file_path)
    if platform.system() != PLATFORM_WINDOWS:
        func_dir_path = func_dir_path.replace("\\", "/")
    func_name = python.__name__
    func_file_name = os.path.splitext(os.path.basename(func_file_path))[0]

    return (func_name, func_file_name, func_dir_path)
