from os.path import expanduser

CONFIGS = expanduser("~/.config.cfg")


DEFAULT_PREPROCESSING = {
    "video": {"fps": 30, "max_side": 720, "num_jobs": 4, "min_fps": 10},
    "image": {
        "compress_ratio": 100,
        "max_side": 720,
        "num_jobs": 8,
    },
}

DEFAULT_POSTPROCESSING = {
    "video": {
        "fps": 30,
        "max_side": 1920,
        "big_only": True,
        "num_jobs": 4,
        "min_fps": 10,
    },
    "image": {
        "compress_ratio": 100,
        "max_side": 1920,
        "big_only": True,
        "num_jobs": 8,
    },
}
