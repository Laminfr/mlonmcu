import sys
import git
import logging
from pathlib import Path
import venv
import os
from .list import get_environment_names, get_alternative_name, register_environment
from .config import (
    get_environments_dir,
    env_subdirs,
    get_config_dir,
    get_environments_file,
    DEFAULTS,
    init_config_dir,
)
from .templates import write_environment_yaml_from_template
from .util import in_virtualenv
from mlonmcu.logging import get_logger

logger = get_logger()


def create_environment_directories(path, directories):
    if not isinstance(path, Path):
        path = Path(path)
    if not path.is_dir():
        raise RuntimeError(f"Not a diretory: {path}")
    for directory in directories:
        (path / directory).mkdir(parents=True, exist_ok=True)


def clone_models_repo(
    dest, url="https://github.com/tum-ei-eda/mlonmcu-models.git"
):  # FIXME: update URL
    git.Git(dest).clone(url)


def ask_user(text, default: bool, yes_keys=["y", "j"], no_keys=["n"], interactive=True):
    assert len(yes_keys) > 0 and len(no_keys) > 0
    if not interactive:
        return default
    if default:
        suffix = " [{}/{}] ".format(yes_keys[0].upper(), no_keys[0].lower())
    else:
        suffix = " [{}/{}] ".format(yes_keys[0].lower(), no_keys[0].upper())
    message = text + suffix
    answer = input(message)
    if default:
        return answer.lower() not in no_keys and answer.upper() not in no_keys
    else:
        return not (answer.lower() not in yes_keys and answer.upper() not in yes_keys)


def create_venv_directory(base, hidden=True):
    if not isinstance(base, Path):
        base = Path(base)
    dirname = ".venv" if hidden else "venv"
    venv_dir = base / dirname
    venv.create(venv_dir)
    print(
        f"Virtual environment was created in {venv_dir}. Make sure to activate it before using mlonmcu."
    )


def initialize_environment(
    directory,
    name,
    interactive=True,
    create_venv=None,
    clone_models=None,
    allow_exists=None,
    register=None,
    template=None,
):
    assert template != None
    print("Initializing ML on MCU environment")
    use_default_dir = directory == get_environments_dir()
    has_name = len(name.strip()) > 0
    if has_name:
        final_name = name.strip()
    else:
        if use_default_dir:
            final_name = DEFAULTS["environment"]
        else:
            final_name = "unamed"
    if use_default_dir:
        target_dir = os.path.join(directory, final_name)
    else:
        target_dir = directory
    target_dir = os.path.abspath(target_dir)
    config_dir = get_config_dir()
    if use_default_dir or register != False:
        if not os.path.exists(config_dir):
            print(
                f"The mlonmcu user config directory {config_dir} does not exist!",
                end=" - ",
            )
            if not ask_user("Initialize?", default=True, interactive=interactive):
                print("Aborting...")
                sys.exit(1)
            init_config_dir()
            print("Initialized config directory.")

    print("Selected target directory:", target_dir)
    if os.path.exists(target_dir):
        print("The directory already exists!")
        if len(os.listdir(target_dir)) > 0:
            print("The directory is not empty!", end=" - ")
            # TODO: check for mlonmcu project files, if yes ask for overwrite instead
            if not allow_exists or (allow_exists is None and not ask_user("Use anyway?", default=False, interactive=interactive)):
                print("Aborting...")
                sys.exit(1)
        print("Using existing directory.")
    else:
        print("The directory does not exist!", end=" - ")
        if not ask_user("Create directory?", default=True, interactive=interactive):
            print("Aborting...")
            sys.exit(1)
        Path(target_dir).mkdir()
        print("Created directory.")
    print(f"Creating environment.yml based on template '{template}'.")
    # TODO: create and maintain environments.yml in user directory?
    write_environment_yaml_from_template(
        os.path.join(target_dir, "environment.yml"), template, home_dir=target_dir
    )

    # FIXME: controversial?
    if create_venv is None:
        if not in_virtualenv():
            print(
                "It is strongly recommended to use mlonmcu inside a virtual Python environment."
            )
            if ask_user(
                "Create one automatically?", default=False, interactive=interactive
            ):
                # TODO: create venv
                create_venv_directory(target_dir)
        else:
            print("Skipping creation of virtual environment. (already inside one)")
    else:
        if create_venv:
            print("The creation of a virtual environment was requested")
            create_venv_directory(target_dir)
        else:
            print("Skipping creation of virtual environment.")

    subdirs = env_subdirs
    if clone_models or (
        clone_models is None
        and ask_user(
            "Clone mlonmcu-models repository into environment?",
            default=False,
            interactive=interactive,
        )
    ):
        clone_models_repo(os.path.join(target_dir, "models"))
        subdirs.append("models")

    print("Initializing directories in environment:", " ".join(subdirs))
    create_environment_directories(target_dir, subdirs)

    if register or (
        register is None
        and ask_user(
            "Should the new environment be added to your list of environments?",
            default=has_name,
            interactive=interactive,
        )
    ):
        environments_file = get_environments_file()
        if not os.path.isfile(environments_file):
            print(f"Environments file ({environments_file}) does not exist!", end=" - ")
            if ask_user("Create empty one?", default=True, interactive=interactive):
                open(environments_file, "a").close()
                print("Initialized empty environments file.")

        env_names = get_environment_names()
        if final_name in env_names:
            alternative_name = get_alternative_name(final_name, env_names)
            print(
                f"An environment with the name '{final_name}' already exists. Using '{alternative_name}' instead"
            )
            final_name = alternative_name
        print("Adding new environment to environments file.")
        register_environment(final_name, target_dir)

    print(
        f"Finished. Please add `export MLONMCU_HOME={target_dir}` to your shell configuration to use it anywhere"
    )
