import pytest
from pathlib import Path

from context_menu.utils import get_method_info, PLATFORM_LINUX, PLATFORM_WINDOWS
from conftest import mock_platform


@pytest.mark.parametrize(
    "platform_name,expected_func_dir_path",
    ((PLATFORM_WINDOWS, "context_menu\\tests"), (PLATFORM_LINUX, "context_menu/tests")),
)
def test_method_info(platform_name: str, expected_func_dir_path: str) -> None:
    """Tests get_method_info returns the correct information."""

    def example_func() -> None:
        pass

    with mock_platform(platform_name):
        func_name, func_file_name, func_dir_path = get_method_info(example_func)

    assert func_name == "example_func"
    assert func_file_name == "test_utils"

    # Ensure that we have the correct slashes
    assert func_dir_path.endswith(expected_func_dir_path)
    assert Path(func_dir_path).name == "tests"
