
import logging
import logging.config
import sys

LOGGERS = []

logging.basicConfig(
    format='%(asctime)s : %(levelname)-16s %(name)-32s %(message)-32s',
    filename="/dev/null",
    level=logging.CRITICAL
)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})


def getLogger(package, compenent="/"):
    from Constants import LOGGING
    logger = logging.getLogger(package)
    if str(package+compenent) not in LOGGERS:
        logger.handlers.clear()
        handler = logging.StreamHandler(sys.stdout)
        compenent = compenent + \
            ''.join([" " for _ in range(24-len(compenent))])
        formatter = logging.Formatter(
            f'%(asctime)s : %(levelname)-12s %(name)-24s  {compenent} %(message)-24s')
        handler.setFormatter(formatter)
        if LOGGING:
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        LOGGERS.append(str(package+compenent))
    return logger
