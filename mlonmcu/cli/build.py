"""Command line subcommand for the build process."""

import copy

import mlonmcu
from mlonmcu.flow import get_available_backend_names
import mlonmcu.flow.tflite
import mlonmcu.flow.tvm
from mlonmcu.models.model import Model
from mlonmcu.session.run import Run
from mlonmcu.session.session import Session
from mlonmcu.cli.common import (
    add_common_options,
    add_context_options,
    add_model_options,
    add_flow_options,
)
from mlonmcu.cli.load import handle as handle_load, add_load_options, add_model_options
from mlonmcu.flow import SUPPORTED_BACKENDS


def add_build_options(parser):
    # TODO: rename to build_group
    build_parser = parser.add_argument_group("build options")
    build_parser.add_argument(
        "-b",
        "--backend",
        type=str,
        action="append",
        choices=get_available_backend_names(),
        help="Backends to use (default: %(default)s)",
    )


def get_parser(subparsers, parent=None):
    """ "Define and return a subparser for the build subcommand."""
    parser = subparsers.add_parser(
        "build",
        description="Build model using the ML on MCU flow.",
        parents=[parent] if parent else [],
        add_help=(parent is None),
    )
    parser.set_defaults(func=handle)
    add_model_options(parser)
    add_common_options(parser)
    add_context_options(parser)
    add_build_options(parser)
    add_flow_options(parser)
    return parser


# TODO: move somewhere else
from mlonmcu.feature.feature import FeatureType


def get_cache_flags(features):
    result = {}
    for feature in features:
        if FeatureType.SETUP in type(feature).types():
            feature.add_required_cache_flags(result)
    return result


def _handle(context, args):
    handle_load(args, ctx=context)
    # print(configs)
    # input()
    backends_names = args.backend
    if isinstance(backends_names, list) and len(backend_names) > 0:
        backends = backends_names
    elif isinstance(backends_names, str):
        backends = [backends_names]
    else:
        assert backends_names is None, "TODO"
        frameworks = context.environment.get_default_frameworks()
        backends = []
        for framework in frameworks:
            framework_backends = context.environment.get_default_backends(framework)
            backends.extend(framework_backends)
    assert len(context.sessions) > 0
    session = context.sessions[-1]
    new_runs = []
    for run in session.runs:
        for backend_name in backends:
            new_run = copy.deepcopy(run)
            # TODO: where to add framework features/config?
            backend_cls = SUPPORTED_BACKENDS[backend_name]
            required_keys = backend_cls.REQUIRED
            # TODO: move somewhere else
            cache_flags = get_cache_flags(new_run.features)
            for key in required_keys:
                if key not in new_run.config:
                    flags = cache_flags.get(key, ())
                    if len(context.cache) == 0:
                        raise RuntimeError(
                            "The dependency cache is empty! Make sure `to run `mlonmcu` setup first.`"
                        )
                    if (key, flags) in context.cache:
                        value = context.cache[key, flags]
                        new_run.config[key] = value
                    else:
                        raise RuntimeError(
                            "Dependency cache miss for required key '{key}'. Try re-running `mlonmcu setup`."
                        )
            backend = backend_cls(features=new_run.features, config=new_run.config)
            new_run.backend = backend
            new_runs.append(new_run)
    session.runs = new_runs
    for run in session.runs:
        run.build(context=context)


def handle(args, ctx=None):
    if ctx:
        _handle(ctx, args)
    else:
        with mlonmcu.context.MlonMcuContext(path=args.home, lock=True) as context:
            _handle(context, args)
