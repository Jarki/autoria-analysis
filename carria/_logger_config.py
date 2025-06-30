LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        },
        "extended": {
            "format": "%(asctime)s [%(levelname)s] %(name)s (%(module)s:%(lineno)s) - %(message)s"
        },
    },
    "handlers": {
        "general": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "DEBUG",
        },
        "my_code": {
            "class": "logging.StreamHandler",
            "formatter": "extended",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "carria": {
            "handlers": ["my_code"],
            "level": "INFO",
            "propagate": False
        },
    },
    "root": {
        "handlers": ["general"],
        "level": "INFO",
    },
}
