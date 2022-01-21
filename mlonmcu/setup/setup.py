import time
from tqdm import tqdm

from mlonmcu.logging import get_logger
from mlonmcu.feature.feature import FeatureType
from .tasks import Tasks
from .task import TaskGraph

logger = get_logger()


class Setup:
    """MLonMCU dependency management interface."""

    FEATURES = []

    DEFAULTS = {
        "print_outputs": False,
    }

    REQUIRES = []

    def __init__(self, features=None, config=None, context=None, tasks_factory=Tasks):
        self.config = config if config else {}
        self.features = self.process_features(features)
        self.config = filter_config(self.config, "setup", self.DEFAULTS, self.REQUIRED)
        self.context = context
        self.tasks_factory = tasks_factory
        self.verbose = bool(self.config["print_outputs"])

    def process_features(self, features):
        if features is None:
            return []
        features = get_matching_features(features, FeatureType.SETUP)
        for feature in features:
            # Not need to list features explicitly
            # assert (
            #     feature.name in self.FEATURES
            # ), f"Incompatible feature: {feature.name}"
            feature.add_setup_config(self.config)
        return features

    def get_dependency_order(self):
        self.tasks_factory.reset_changes()
        task_graph = TaskGraph(
            self.tasks_factory.registry.keys(),
            self.tasks_factory.dependencies,
            self.tasks_factory.providers,
        )
        V, E = task_graph.get_graph()
        order = task_graph.get_order()
        order_str = " -> ".join(order)
        logger.debug("Determined dependency order: %s" % order_str)
        return order

    def setup_progress_bar(self, enabled):
        if progress:
            pbar = tqdm(
                total=len(self.tasks_factory.registry),
                desc="Installing dependencies",
                ncols=100,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
            )
            return pbar
        else:
            logger.info("Installing dependencies...")
            return None

    def write_cache_file(self):
        logger.debug("Updating dependency cache")
        cache_file = self.context.environment.paths["deps"].path / "cache.ini"
        self.context.cache.write_to_file(cache_file)

    def install_dependencies(
        self,
        progress=False,
        write_cache=True,
        rebuild=False,
    ):
        assert self.context is not None
        order = self.get_dependency_order()
        pbar = self.setup_progress_bar(progress)
        for task in order:
            func = self.tasks_factory.registry[task]
            func(self.context, progress=progress, rebuild=rebuild, verbose=self.verbose)
            time.sleep(0.1)
            if pbar:
                pbar.update(1)
        if pbar:
            pbar.close()
        self.write_cache_file()
        logger.info("Finished installing dependencies")