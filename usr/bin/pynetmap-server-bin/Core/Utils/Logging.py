
import logging
import logging.config
import sys


logging.basicConfig(
    format='%(asctime)s : %(levelname)-16s %(name)-32s %(message)-32s',
    filename="/dev/null",
    level=logging.CRITICAL
)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})


def getLogger(name):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s : %(levelname)-16s %(name)-32s %(message)-32s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
