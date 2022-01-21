def remove_config_prefix(config, prefix, skip=[]):
    def helper(key):
        return key.split(f"{prefix}.")[-1]

    return {
        helper(key): value
        for key, value in config.items()
        if f"{prefix}." in key and key not in skip
    }


def filter_config(config, prefix, defaults, required_keys):
    cfg = remove_config_prefix(config, prefix, skip=required_keys)
    for required in required_keys:
        value = None
        if required in cfg:
            value = cfg[required]
        elif required in config:
            value = config[required]
            cfg[required] = value
        assert value is not None, f"Required config key can not be None: {required}"

    for key in defaults:
        if key not in cfg:
            cfg[key] = defaults[key]

    for key in cfg:
        if key not in list(defaults.keys()) + required_keys:
            logger.warn("Backend received an unknown config key: %s", key)

    return cfg


def resolve_required_config(required_keys, features=None, config=None, cache=None):
    """Utility which iterates over a set of given config keys and
    resolves their values using the passed config and/or cache.

    Arguments
    ---------
    required_keys : List[str]

    features : List[Feature]

    config : dict

    cache : TaskCache
        Optional task cache parsed from the `cache.ini` file in the `deps` directory.

    Returns
    -------

    """

    def get_cache_flags(features):
        result = {}
        for feature in features:
            if FeatureType.SETUP in type(feature).types():
                feature.add_required_cache_flags(result)
        return result

    ret = {}
    cache_flags = get_cache_flags(features) if features else {}
    for key in required_keys:
        if config is None or key not in config:
            assert (
                cache is not None
            ), "No dependency cache was provided. Either provide a cache or config."
            if len(cache) == 0:
                raise RuntimeError(
                    "The dependency cache is empty! Make sure `to run `mlonmcu` setup first.`"
                )
            flags = cache_flags.get(key, ())
            if (key, flags) in cache:
                value = cache[key, flags]
                ret[key] = value
            else:
                raise RuntimeError(
                    "Dependency cache miss for required key '{key}'. Try re-running `mlonmcu setup`."
                )
        else:
            ret[key] = config[key]

    return ret
