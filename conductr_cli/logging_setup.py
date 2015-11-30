import logging
import sys

# Default python log levels
LOG_LEVEL_DEBUG = logging.getLevelName('DEBUG')
LOG_LEVEL_INFO = logging.getLevelName('INFO')
LOG_LEVEL_WARN = logging.getLevelName('WARN')
LOG_LEVEL_ERROR = logging.getLevelName('ERROR')

# Custom log level for ConductR CLI
LOG_LEVEL_VERBOSE = int((LOG_LEVEL_DEBUG + LOG_LEVEL_INFO) / 2)
LOG_LEVEL_QUIET = int((LOG_LEVEL_INFO + LOG_LEVEL_WARN) / 2)


class ThresholdFilter(logging.Filter):
    def __init__(self, threshold):
        super().__init__()
        self.threshold = threshold

    def filter(self, record):
        return record.levelno < self.threshold


def verbose(self, message, *args, **kwargs):
    self.log(LOG_LEVEL_VERBOSE, message, *args, **kwargs)


def quiet(self, message, *args, **kwargs):
    self.log(LOG_LEVEL_QUIET, message, *args, **kwargs)


def is_verbose_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_VERBOSE)


def is_debug_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_DEBUG)


def is_info_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_INFO)


def is_quiet_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_QUIET)


def is_warn_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_WARN)


def configure_logging(args, output=sys.stdout, err_output=sys.stderr):
    logging.addLevelName(LOG_LEVEL_VERBOSE, 'VERBOSE')
    logging.Logger.verbose = verbose

    logging.addLevelName(LOG_LEVEL_QUIET, 'QUIET')
    logging.Logger.quiet = quiet

    logging.Logger.is_verbose_enabled = is_verbose_enabled
    logging.Logger.is_debug_enabled = is_debug_enabled
    logging.Logger.is_info_enabled = is_info_enabled
    logging.Logger.is_quiet_enabled = is_quiet_enabled
    logging.Logger.is_warn_enabled = is_warn_enabled

    logger = logging.getLogger()
    logger.setLevel('ERROR')

    formatter = logging.Formatter('%(message)s')

    # Clear existing handlers to prevent duplicate log messages
    for handler in logger.handlers:
        logger.removeHandler(handler)

    output_handler = logging.StreamHandler(stream=output)
    output_handler.setFormatter(formatter)
    output_handler.addFilter(ThresholdFilter(LOG_LEVEL_ERROR))
    logger.addHandler(output_handler)

    err_output_handler = logging.StreamHandler(stream=err_output)
    err_output_handler.setFormatter(formatter)
    err_output_handler.setLevel(LOG_LEVEL_ERROR)
    logger.addHandler(err_output_handler)

    conductr_log = logging.getLogger('conductr_cli')
    if args.verbose:
        conductr_log.setLevel('VERBOSE')
    elif args.quiet:
        conductr_log.setLevel('QUIET')
    else:
        conductr_log.setLevel('INFO')
