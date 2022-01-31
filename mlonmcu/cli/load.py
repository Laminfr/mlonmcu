"""Command line subcommand for the load stage."""

import copy

import mlonmcu
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
    kickoff_runs,
)
from mlonmcu.config import resolve_required_config
from .helper.parse import extract_config_and_init_features
from mlonmcu.models import SUPPORTED_FRONTENDS
from mlonmcu.models.lookup import lookup_models, map_frontend_to_model
from mlonmcu.session.run import RunStage


def add_load_options(parser):
    load_parser = parser.add_argument_group("load options")
    # TODO: move model parser here?
    load_parser.add_argument(
        "--frontend",
        type=str,
        metavar="FRONTEND",
        choices=SUPPORTED_FRONTENDS.keys(),
        default=None,
        nargs=1,
        help="Explicitly choose the frontends to use (choices: %(choices)s)",
    )


def get_parser(subparsers):
    """ "Define and return a subparser for the load subcommand."""
    parser = subparsers.add_parser(
        "load", description="Load model using the ML on MCU flow."
    )
    parser.set_defaults(func=handle)
    add_model_options(parser)
    add_common_options(parser)
    add_context_options(parser)
    add_load_options(parser)
    add_flow_options(parser)
    return parser


def init_frontends(frontend_names, features, config, context=None):
    names = []
    if isinstance(frontend_names, list) and len(frontend_names) > 0:
        names = frontend_names
    elif isinstance(frontend_names, str):
        names = [frontend_names]
    else:
        # No need to specify a default, because we just use the provided order in the environment.yml
        assert frontend_names is None, "TODO"
        assert context is not None, "Need context to resolve default frontends"
        all_frontend_names = context.environment.get_enabled_frontends()
        names.extend(all_frontend_names)
    frontends = []
    for frontend_name in names:
        frontend_cls = SUPPORTED_FRONTENDS[frontend_name]
        required_keys = frontend_cls.REQUIRED
        frontend_config = config.copy()
        frontend_config.update(
            resolve_required_config(
                required_keys,
                features=features,
                config=config,
                cache=context.cache if context else None,
            )
        )
        try:
            frontend = frontend_cls(features=features, config=frontend_config)
        except Exception as err:
            raise RuntimeError() from err
            print("Frontend could not be initialized. Continuing with next one...")
            continue
        frontends.append(frontend)
    assert (
        len(frontends) > 0
    ), "Could not initialize at least one frontend for the given set of features"
    return frontends


def _handle(context, args):
    model_names = args.models
    config, features = extract_config_and_init_features(args)
    frontends = init_frontends(
        args.frontend, features=features, config=config, context=context
    )
    model_hints = lookup_models(model_names, frontends=frontends, context=context)
    session = context.get_session()
    for hint in model_hints:
        model, frontend = map_frontend_to_model(
            hint, frontends, backend=None
        )  # TODO: we do not yet know the backend...
        # run = Run(model=model, features=features, config=config)
        run = session.create_run(model=model, features=features, config=config)
        run.add_frontend(frontend)
        # session.runs.append(run)
    # for run in session.runs:
    #     run.load(context=context)


def handle(args, ctx=None):
    if ctx:
        _handle(ctx, args)
    else:
        with mlonmcu.context.MlonMcuContext(path=args.home, lock=True) as context:
            _handle(context, args)
            kickoff_runs(args, RunStage.LOAD, context)
