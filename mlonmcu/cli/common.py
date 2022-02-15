import os
import multiprocessing
import logging
from mlonmcu.target import SUPPORTED_TARGETS
from mlonmcu.feature.features import get_available_feature_names
from mlonmcu.logging import get_logger, set_log_level
from .helper.parse import extract_config


def handle_logging_flags(args):
    if hasattr(args, "verbose") and hasattr(args, "quiet"):
        if args.verbose and args.quiet:
            raise RuntimeError("--verbose and --quiet can not be used at the same time")
        elif args.verbose:
            set_log_level(logging.DEBUG)
        elif args.quiet:
            set_log_level(logging.WARNING)
        else:
            set_log_level(logging.INFO)


def add_flow_options(parser):
    flow_parser = parser.add_argument_group("flow options")
    flow_parser.add_argument(  # TODO: move to compile.py?
        "-t",
        "--target",
        type=str,
        metavar="TARGET",
        choices=SUPPORTED_TARGETS.keys(),
        action="append",
        # default=None,
        # nargs=1,
        help="The target device/architecture (choices: %(choices)s)",
    )
    flow_parser.add_argument(
        "-f",
        "--feature",
        type=str,
        metavar="FEATURE",
        # nargs=1,
        action="append",
        choices=get_available_feature_names(),
        help="Enabled features for target/framework/backend (choices: %(choices)s)",
    )
    flow_parser.add_argument(
        "-c",
        "--config",
        metavar="KEY=VALUE",
        nargs="+",
        action="append",
        help="Set a number of key-value pairs "
        "(do not put spaces before or after the = sign). "
        "If a value contains spaces, you should define "
        "it with double quotes: "
        'foo="this is a sentence". Note that '
        "values are always treated as strings.",
    )
    flow_parser.add_argument(
        "--parallel",
        metavar="THREADS",
        nargs="?",
        type=int,
        const=multiprocessing.cpu_count(),
        default=1,
        help="Use multiple threads to process runs in parallel (%(const)s if specified, else %(default)s)",
    )
    flow_parser.add_argument(
        "-p",
        "--progress",
        action="store_true",
        help="Display progress bar (default: %(default)s)",
    )
    flow_parser.add_argument(
        "--resume",
        action="store_true",
        help="Try to resume the latest session (default: %(default)s)",
    )


def add_common_options(parser):
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed messages for easier debugging (default: %(default)s)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Reduce number of logging statements to a minimum (default: %(default)s)",
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Execute run.py inside docker container (default: %(default)s)",
    )


def add_context_options(parser, with_home=True):
    common = parser.add_argument_group("context options")
    if with_home:
        home = os.getenv("MLONMCU_HOME", None)
        common.add_argument(
            "-H",
            "--home",
            "--hint",
            type=str,
            default=home,
            help="The path to the mlonmcu environment (overwriting $MLONMCU_HOME environment variable)",
        )


def add_model_options(parser):
    parser.add_argument(
        "models",
        metavar="model",
        type=str,
        nargs="+",
        default=None,
        help="Model to process",
    )


def kickoff_runs(args, until, context):
    assert len(context.sessions) > 0
    session = context.sessions[-1]
    config = extract_config(args)
    per_stage = True
    if "runs_per_stage" in config:
        per_stage = bool(config["runs_per_stage"])
    elif "runs_per_stage" in context.environment.vars:
        per_stage = bool(context.environment.vars["runs_per_stage"])
    session.process_runs(
        until=until,
        per_stage=per_stage,
        num_workers=args.parallel,
        progress=args.progress,
        context=context,
        export=True,
    )
