from __future__ import annotations
from typing import TYPE_CHECKING
import pytest

from context_menu import menus
from context_menu.utils import PLATFORM_LINUX, PLATFORM_WINDOWS
from conftest import mock_platform


if TYPE_CHECKING:
    from typing import Any


def foo2(filenames, params):
    print("foo2")
    print(filenames)
    input()


def foo3(filenames, params):
    print("foo3")
    print(filenames)
    input()


@pytest.fixture
def foo_menu():
    cm = menus.ContextMenu("Foo menu", type="FILES")
    cm2 = menus.ContextMenu("Foo Menu 2")
    cm3 = menus.ContextMenu("Foo Menu 3")
    cm3.add_items(
        [
            menus.ContextCommand("Foo One", command="echo hello > example.txt"),
        ]
    )
    cm2.add_items(
        [
            menus.ContextCommand("Foo Two", python=foo2),
            cm3,
        ]
    )
    cm.add_items([cm2, menus.ContextCommand("Foo Three", python=foo3)])

    yield cm


@pytest.mark.parametrize(
    "platform_name,expected_class",
    ((PLATFORM_WINDOWS, menus.RegistryMenu), (PLATFORM_LINUX, menus.NautilusMenu)),
)
def test_context_menu_class(platform_name: str, expected_class: Any) -> None:
    """Tests ContextMenu returns the correct implementation."""
    with mock_platform(platform_name):
        assert isinstance(menus.ContextMenu("Test Menu", "FILES"), expected_class)


@pytest.mark.parametrize(
    "platform_name,expected_class",
    (
        (PLATFORM_WINDOWS, menus.FastRegistryCommand),
        (PLATFORM_LINUX, menus.FastNautilusCommand),
    ),
)
def test_fast_command_class(platform_name: str, expected_class: Any) -> None:
    """Tests FastCommand returns the correct implementation."""
    with mock_platform(platform_name):
        assert isinstance(menus.FastCommand("Test", "FILES"), expected_class)


def test_fast_command_value_error() -> None:
    """Tests ValueError is correctly raised with both command and python."""

    def foo() -> None:
        pass

    with pytest.raises(ValueError):
        menus.FastCommand("Test", "FILES", command="echo Hello", python=foo)
