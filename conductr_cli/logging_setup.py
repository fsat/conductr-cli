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


def configure_logging(args, output=sys.stdout, err_output=sys.stderr):
    logging.addLevelName(LOG_LEVEL_VERBOSE, 'VERBOSE')
    logging.Logger.verbose = verbose

    logging.addLevelName(LOG_LEVEL_QUIET, 'QUIET')
    logging.Logger.quiet = quiet

    logger = logging.getLogger()
    logger.setLevel('ERROR')

    formatter = logging.Formatter('%(message)s')

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
