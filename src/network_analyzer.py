"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import logging
logger = logging.getLogger(__name__)


class NetworkAnalyzer(object):
    def __init__(self) -> None:
        logger.info('Initialised network analyzer.')

    def run(self) -> list:
        while True:
            array: list = []
            logger.info('Read network vector values.')
            return array