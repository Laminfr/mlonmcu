"""Command line subcommand for initializing a mlonmcu environment."""

import sys
import os
import pkg_resources
import pkgutil
import jinja2

from mlonmcu.environment.templates import get_template_names
from mlonmcu.environment.config import get_environments_dir, DEFAULTS, env_subdirs
from mlonmcu.utils import in_virtualenv
from mlonmcu.environment.init import initialize_environment


def add_init_options(parser):
    init_parser = parser.add_argument_group("init options")
    init_parser.add_argument(
        "-n",
        "--name",
        metavar="NAME",
        nargs=1,
        type=str,
        default="",
        help="Environment name (default: %(default)s)",
    )
    init_parser.add_argument(
        "-t",
        "--template",
        metavar="TEMPLATE",
        nargs=1,
        type=str,
        choices=get_template_names(),
        default=DEFAULTS["template"],
        help="Environment template (default: %(default)s, allowed: %(choices)s)",
    )
    init_parser.add_argument(
        "DIR",
        nargs="?",
        type=str,
        default=get_environments_dir(),
        help="Environment directory (default: " + os.path.join(get_environments_dir(), "{NAME}") + ")",
    )
    init_parser.add_argument(
        "--non-interactive",
        dest="non_interactive",
        action="store_true",
        help="Do not ask questions interactively",
    )
    init_parser.add_argument(
        "--venv",
        default=None,
        action="store_true",
        help="Create virtual python environment",
    )
    init_parser.add_argument(
        "--clone-models",
        dest="clone_models",
        default=None,
        action="store_true",
        help="Clone models directory into environment",
    )
    init_parser.add_argument(
        "--skip-sw",
        dest="skip_sw",
        default=None,
        action="store_true",
        help="Clone sw directory into environment",
    )
    init_parser.add_argument(
        "--register",
        default=None,
        action="store_true",
        help="Add environment to the list of environment for the current user",
    )
    init_parser.add_argument(
        "--allow-exists",
        dest="allow_exists",
        default=None,
        action="store_true",
        help="Allow overwriting an existing environment directory",
    )


def get_parser(subparsers):
    """ "Define and return a subparser for the init subcommand."""
    parser = subparsers.add_parser("init", description="Initialize ML on MCU environment.")
    parser.set_defaults(func=handle)
    add_init_options(parser)
    return parser


def handle(args):
    """Callback function which will be called to process the init subcommand"""
    name = args.name[0] if isinstance(args.name, list) else args.name
    initialize_environment(
        args.DIR,
        name,
        create_venv=args.venv,
        interactive=not args.non_interactive,
        clone_models=args.clone_models,
        skip_sw=args.skip_sw,
        register=args.register,
        template=args.template[0] if isinstance(args.template, list) else args.template,
        allow_exists=args.allow_exists,
    )
