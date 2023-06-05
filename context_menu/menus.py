from __future__ import annotations
from typing import TYPE_CHECKING
import os
import platform

if TYPE_CHECKING:
    from typing import Union, Literal
    from types import FunctionType

    ActivationType = Literal["FILES", "DIRECTORY", "DIRECTORY_BACKGROUND", "DRIVE"]
    CommandVar = Literal["FILENAME", "DIR", "DIRECTORY", "PYTHONLOC"]
    ItemType = Union["ContextMenu", "ContextCommand"]

from context_menu import linux_menus, windows_menus
from context_menu.utils import get_method_info, PLATFORM_LINUX, PLATFORM_WINDOWS


class ContextMenu:
    """The general menu class.

    This class generalizes the menus and eventually passes the correct values
    to the platform-specifically menus.
    """

    def __init__(self, name: str, type: ActivationType | str | None = None) -> None:
        """
        Only specify type if it's the root menu.
        """
        self.name = name
        self.sub_items: list[ItemType] = []
        self.type = type
        self.isMenu = True  # Needed to avoid circular imports

    def __new__(cls, *args, **kwargs):
        if cls is ContextMenu:
            cls = (
                RegistryMenu if platform.system() == PLATFORM_WINDOWS else NautilusMenu
            )
        return object.__new__(cls)

    def add_items(self, items: list[ItemType]) -> None:
        """
        Adds a list of items to the current menu.
        """
        self.sub_items.extend(items)

    def compile(self) -> None:
        """Creates the actual menu."""
        raise NotImplementedError()


class ContextCommand:
    """The general command class.

    A command is an executable entry in a context-menu, where menus hold other commands.

    Name = Name of the command
    Command = command to be ran from the shell
    python = function to be ran
    params = any other parameters to be passed
    command_vars = to help with the command
    """

    def __init__(
        self,
        name: str,
        command: str | None = None,
        python: FunctionType | None = None,
        params: str = "",
        command_vars: list[CommandVar] | None = None,
    ) -> None:
        """
        Do not specify both 'python' and 'command', either pass a python function or a command but not both.
        """
        self.name = name
        self.command = command
        self.isMenu = False
        self.python = python
        self.params = params
        self.command_vars = command_vars

        if command != None and python != None:
            raise ValueError("both command and python cannot be defined")

    def get_platform_command(self):
        """
        Will be used in future changes.
        """
        return self.command[platform.system().lower()]


class FastCommand:
    """Used for fast creation of a command.

    Good if you don't want to get too involved and just jump start a program.
    Extremely similar methods to other classes, only slightly modified. View the
    documentation of the above classes for info on these methods.
    """

    def __init__(
        self,
        name: str,
        type: ActivationType | str,
        command: str | None = None,
        python: FunctionType | None = None,
        params: str = "",
        command_vars: list[CommandVar] | None = None,
    ) -> None:
        self.name = name
        self.type = type
        self.command = command
        self.python = python
        self.params = params
        self.command_vars = command_vars

        if command != None and python != None:
            raise ValueError("both command and python cannot be defined")

    def __new__(cls, *args, **kwargs):
        if cls is FastCommand:
            cls = (
                FastRegistryCommand
                if platform.system() == PLATFORM_WINDOWS
                else FastNautilusCommand
            )
        return object.__new__(cls)

    def compile(self) -> None:
        """Creates the actual command."""
        raise NotImplementedError()


try:

    def removeMenu(name: str, type: ActivationType | str) -> None:
        """
        Removes a menu/command entry from a context menu.

        Requires the name of the menu and type of the menu
        """

        if platform.system() == PLATFORM_LINUX:
            linux_menus.remove_linux_menu(name)
        if platform.system() == PLATFORM_WINDOWS:
            windows_menus.remove_windows_menu(name, type)

except Exception as e:
    # For testing
    print(e)
    pass


# Linux implementation ------------------------------


class NautilusMenu(ContextMenu):
    """ContextMenu subclass for Linux systems.

    On a Linux system, instantiating a ContextMenu should return this object.
    """

    def __init__(self, name: str, type: ActivationType | str | None = None) -> None:
        """
        Items required are the name of the top menu, the sub items, and the type.
        """
        # nautilus extensions doesn't work with filenames with spaces
        # Example menu item -> ExampleMenuItem
        name = (
            "".join([word.title() for word in name.split()])
            if len(name.split()) > 0
            else name
        )
        super(NautilusMenu, self).__init__(name, type)
        self.counter = 0

        # Create all the necessary lists that will be used later on
        self.commands: list[str] = []
        self.script_dirs: list[str] = []
        self.funcs: list[str] = []
        self.imports: list[str] = []

    if platform.system() != PLATFORM_LINUX:

        def __new__(cls, *args, **kwargs):
            raise NotImplementedError(
                f"cannot instantiate {cls.__name__!r} on your system"
            )

    def compile(self) -> None:
        if self.type is None:
            raise Exception("type can't be None for top-level ContextMenu")

        code = linux_menus.build_script(self)
        save_loc = os.path.join(os.path.expanduser("~"), ".local/share/")
        print(save_loc)
        save_loc = linux_menus.create_path(save_loc, "nautilus-python")
        save_loc = linux_menus.create_path(save_loc, "extensions")
        save_loc = os.path.join(save_loc, f"{self.name}.py")
        py_file = open(save_loc, "w")
        py_file.write(code)
        py_file.close()


class FastNautilusCommand(FastCommand):
    """FastCommand subclass for Linux systems.

    On a Linux system, instantiating a FastCommand should return this object.
    """

    if platform.system() != PLATFORM_LINUX:

        def __new__(cls, *args, **kwargs):
            raise NotImplementedError(
                f"cannot instantiate {cls.__name__!r} on your system"
            )

    def compile(self) -> None:
        # Has to be done here because of cyclic imports
        menu = NautilusMenu(
            self.name,
            self.type,
        )
        menu.add_items(
            [
                ContextCommand(
                    self.name,
                    command=self.command,
                    python=self.python,
                    params=self.params,
                    command_vars=self.command_vars,
                )
            ]
        )
        menu.compile()


# Windows implementation ------------------------------


class RegistryMenu(ContextMenu):
    """ContextMenu subclass for Windows systems.

    On a Windows system, instantiating a ContextMenu should return this object.
    """

    if platform.system() != PLATFORM_WINDOWS:

        def __new__(cls, *args, **kwargs):
            raise NotImplementedError(
                f"cannot instantiate {cls.__name__!r} on your system"
            )

    def compile(
        self, items: list[ItemType] | None = None, path: str | None = None
    ) -> None:
        if items is None:
            # top-level ContextMenu
            if self.type is None:
                raise Exception("type can't be None for top-level ContextMenu")

            # run_admin()
            items = self.sub_items
            path = windows_menus.context_registry_format(self.type)
            path = windows_menus.create_menu(self.name, path)

        assert items is not None
        assert path is not None
        for item in items:
            if isinstance(item, ContextMenu):
                # if the item is a menu
                assert isinstance(item, RegistryMenu)
                submenu_path = windows_menus.create_menu(item.name, path)
                item.compile(items=item.sub_items, path=submenu_path)
                continue

            # Otherwise the item is a command
            if item.command is not None:
                if item.command_vars is not None:
                    # If the item has to be ran from os.system
                    new_command = windows_menus.create_shell_command(
                        item.command, item.command_vars
                    )
                    windows_menus.create_command(item.name, path, new_command)
                else:
                    # The item is just a plain old command
                    windows_menus.create_command(item.name, path, item.command)
            elif item.python is not None:
                # If a Python function is defined
                func_name, func_file_name, func_dir_path = get_method_info(item.python)
                new_command = None
                if self.type in ["DIRECTORY_BACKGROUND", "DESKTOP_BACKGROUND"]:
                    # If it requires a background command
                    new_command = windows_menus.create_directory_background_command(
                        func_name, func_file_name, func_dir_path, item.params
                    )
                else:
                    # If it requires a file command
                    new_command = windows_menus.create_file_select_command(
                        func_name, func_file_name, func_dir_path, item.params
                    )

                windows_menus.create_command(item.name, path, new_command)
            else:
                assert False, "Missing a command or python function"


class FastRegistryCommand(FastCommand):
    """FastCommand subclass for Windows systems.

    On a Windows system, instantiating a FastCommand should return this object.
    """

    if platform.system() != PLATFORM_WINDOWS:

        def __new__(cls, *args, **kwargs):
            raise NotImplementedError(
                f"cannot instantiate {cls.__name__!r} on your system"
            )

    def compile(self) -> None:
        # run_admin()

        path = windows_menus.context_registry_format(self.type)
        key_path = windows_menus.join_keys(path, self.name)
        windows_menus.create_key(key_path)

        command_path = windows_menus.join_keys(key_path, "command")
        windows_menus.create_key(command_path)

        if self.command is not None:
            if self.command_vars is not None:
                # If it has command_vars
                new_command = windows_menus.create_shell_command(
                    self.command, self.command_vars
                )
            else:
                new_command = self.command
        elif self.python is not None:
            # If a python function is defined
            func_name, func_file_name, func_dir_path = get_method_info(self.python)
            if self.type in ["DIRECTORY_BACKGROUND", "DESKTOP_BACKGROUND"]:
                # If it requires a background selection
                new_command = windows_menus.create_directory_background_command(
                    func_name, func_file_name, func_dir_path, self.params
                )
            else:
                # If it requires a file selection
                new_command = windows_menus.create_file_select_command(
                    func_name, func_file_name, func_dir_path, self.params
                )
        else:
            assert False, "Missing a command or python function"

        windows_menus.set_key_value(command_path, "", new_command)
