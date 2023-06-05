# all imports ---------------
from __future__ import annotations
from typing import TYPE_CHECKING
import os
import ctypes
import sys

if TYPE_CHECKING:
    from typing import Any
    from context_menu.menus import (
        ActivationType,
        CommandVar,
    )


# registry_shortcuts.py ----------------------------------------------------------------------------------------

try:
    import winreg

    # ------------------------------------------------------------------

    def is_admin() -> bool:
        """
        Returns True if the current python instance has admin, and false otherwise.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def run_admin(params: str = sys.argv[0], force: bool = False) -> None:
        """
        If the python instance does not have admin priviledges, it stops the current execution and runs the program as admin.

        You can customize where it runs/Force it to run regardless.
        """
        if not is_admin() or force:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
            sys.exit()

    # ------------------------------------------------------------------

    def create_key(path: str, hive: int = winreg.HKEY_CURRENT_USER) -> None:
        """
        Creates a key at the desired path.
        """
        winreg.CreateKey(hive, path)

    def set_key_value(
        key_path: str,
        subkey_name: str,
        value: str | int,
        hive: int = winreg.HKEY_CURRENT_USER,
    ) -> None:
        """
        Changes the value of a subkey. Creates the subkey if it doesn't exist.
        """
        with winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE) as open_key:
            winreg.SetValueEx(open_key, subkey_name, 0, winreg.REG_SZ, value)

    def get_key_value(
        key_path: str,
        subkey_name: str,
        hive: int = winreg.HKEY_CURRENT_USER,
    ) -> Any:
        """
        Changes the value of a subkey. Creates the subkey if it doesn't exist.
        """
        with winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE) as open_key:
            return winreg.QueryValueEx(open_key, subkey_name)[0]

    def get_key_value(
        key_path: str,
        subkey_name: str,
        hive: int = winreg.HKEY_CURRENT_USER,
    ) -> Any:
        """
        Gets the value of a subkey.
        """
        with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as open_key:
            return winreg.QueryValueEx(open_key, subkey_name)[0]

    def list_keys(path: str, hive: int = winreg.HKEY_CURRENT_USER) -> list[str]:
        """
        Returns a list of all the keys at a given registry path.
        """
        with winreg.OpenKey(hive, path) as open_key:
            key_amt = winreg.QueryInfoKey(open_key)[0]
            keys = []

            for count in range(key_amt):
                subkey = winreg.EnumKey(open_key, count)
                keys.append(subkey)

            return keys

    def delete_key(path: str, hive: int = winreg.HKEY_CURRENT_USER) -> None:
        """
        Deletes the desired key and all other subkeys at the given path.
        """
        open_key = winreg.OpenKey(hive, path)
        subkeys = list_keys(path)

        if len(subkeys) > 0:
            for key in subkeys:
                delete_key(path + "\\" + key)
        winreg.DeleteKey(open_key, "")

except:

    def create_key(path: str, hive: int = 0) -> None:
        """
        Creates a key at the desired path.
        """
        raise NotImplementedError("winreg is not available on this platform")

    def set_key_value(
        key_path: str, subkey_name: str, value: str | int, hive: int = 0
    ) -> None:
        """
        Changes the value of a subkey. Creates the subkey if it doesn't exist.
        """
        raise NotImplementedError("winreg is not available on this platform")

    def get_key_value(key_path: str, subkey_name: str, hive: int = 0) -> Any:
        """
        Gets the value of a subkey.
        """
        raise NotImplementedError("winreg is not available on this platform")

    def list_keys(path: str, hive: int = 0) -> list[str]:
        """
        Returns a list of all the keys at a given registry path.
        """
        raise NotImplementedError("winreg is not available on this platform")

    def delete_key(path: str, hive: int = 0) -> None:
        """
        Deletes the desired key and all other subkeys at the given path.
        """
        raise NotImplementedError("winreg is not available on this platform")

    print("Not windows")


# advanced_reg_config.py ----------------------------------------------------------------------------------------


# These are the paths in the registry that correlate to when the context menu is fired.
# For example, FILES is when a file is right clicked
CONTEXT_SHORTCUTS = {
    "FILELOC": "Software\\Classes",
    "FILES": "Software\\Classes\\*\\shell",
    "DIRECTORY": "Software\\Classes\\Directory\\shell",
    "DIRECTORY_BACKGROUND": "Software\\Classes\\Directory\\Background\\shell",
    "DRIVE": "Software\\Classes\\Drive\\shell",
}

# Not used yet, but could be useful in the future
COMMAND_PRESETS = {
    "python": sys.executable,
    "pythonw": os.path.join(os.path.dirname(sys.executable), "pythonw.exe"),
}

COMMAND_VARS = {
    "FILENAME": "' '.join(sys.argv[1:]) ",
    "DIR": "os.getcwd()",
    "DIRECTORY": "os.getcwd()",
    "PYTHONLOC": "sys.executable",
}


def join_keys(*keys: str) -> str:
    """Joins parts of a registry path.

    This joins the parts with \\ unlike os.path.join that would
    use / on Linux and break tests.

    :param keys: parts of the registry path
    :return: complete registry path
    """
    return "\\".join(keys)


def context_registry_format(item: str) -> str:
    """
    Converts a verbose type into a registry path.

    For example, 'FILES' -> 'Software\\Classes\\*\\shell'
    """
    item = item.upper()
    if "." in item:
        return join_keys(CONTEXT_SHORTCUTS["FILELOC"], item.lower(), "shell")
    return CONTEXT_SHORTCUTS[item]


def command_preset_format(item: str) -> str:
    """
    Converts a python string to an executable location.

    For example, 'python' -> sys.executable
    """
    return COMMAND_PRESETS[item.lower()]


def command_var_format(item: str) -> str:
    """
    Converts a python string to a value for a command

    """
    return COMMAND_VARS[item.upper()]


def create_file_select_command(
    func_name: str, func_file_name: str, func_dir_path: str, params: str
) -> str:
    """
    Creates a registry valid command to link a context menu entry to a funtion, specifically for file selection(FILES, DIRECTORY, DRIVE).

    Requires the name of the function, the name of the file, and the path to the directory of the file.
    """
    python_loc = sys.executable
    sys_section = f"""import sys; sys.path.insert(0, '{func_dir_path}')""".replace(
        "\\", "/"
    )
    file_section = f"import {func_file_name}"
    dir_path = """' '.join(sys.argv[1:]) """
    func_section = f"""{func_file_name}.{func_name}([{dir_path}],'{params}')"""
    python_portion = (
        f'''"{python_loc}" -c "{sys_section}; {file_section}; {func_section}"'''
    )
    full_command = f'''{python_portion} \"%1\"'''

    return full_command


def create_directory_background_command(
    func_name: str, func_file_name: str, func_dir_path: str, params: str
) -> str:
    """
    Creates a registry valid command to link a context menu entry to a funtion, specifically for backgrounds(DIRECTORY_BACKGROUND, DESKTOP_BACKGROUND).

    Requires the name of the function, the name of the file, and the path to the directory of the file.
    """
    python_loc = sys.executable
    sys_section = (
        f"""import sys; import os; sys.path.insert(0, '{func_dir_path}')""".replace(
            "\\", "/"
        )
    )
    file_section = f"import {func_file_name}"
    dir_path = "os.getcwd()"
    func_section = f"""{func_file_name}.{func_name}([{dir_path}],'{params}')"""
    full_command = (
        f'''"{python_loc}" -c "{sys_section}; {file_section}; {func_section}"'''
    )

    return full_command


def create_shell_command(command: str, command_vars: list[CommandVar]) -> str:
    """
    Creates a shell command and replaces '?' with the command_vars list
    """

    transformed_vars = [
        "' + " + command_var_format(item) + " + '" for item in command_vars
    ]
    new_command = command.replace("?", "{}").format(*transformed_vars)
    python_section = """import os; import sys; os.system('{}')""".format(new_command)
    full_command = '"{}" -c "{}" "%1"'.format(sys.executable, python_section)
    return full_command


# windows_menus.py ----------------------------------------------------------------------------------------


def create_menu(name: str, path: str) -> str:
    """
    Creates a menu with the given name and path.

    Used in the compile method.
    """
    key_path = join_keys(path, name)
    create_key(key_path)

    set_key_value(key_path, "MUIVerb", name)
    set_key_value(key_path, "subcommands", "")

    key_shell_path = join_keys(key_path, "shell")
    create_key(key_shell_path)

    return key_shell_path


def create_command(name: str, path: str, command: str) -> None:
    """
    Creates a key with a command subkey with the 'name' and 'command', at path 'path'.
    """
    key_path = join_keys(path, name)
    create_key(key_path)
    set_key_value(key_path, "", name)

    command_path = join_keys(key_path, "command")
    create_key(command_path)
    set_key_value(command_path, "", command)


# Testing section...

try:

    def remove_windows_menu(name: str, type: ActivationType | str) -> None:
        """
        Removes a context menu from the windows registry.
        """
        # run_admin()
        menu_path = join_keys(context_registry_format(type), name)
        delete_key(menu_path)

except Exception:
    pass
    # for testing
