"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import logging
import numpy
from rohdeschwarz.instruments.vna import Vna
logger = logging.getLogger(__name__)


class NetworkAnalyzer(object):
    def __init__(self) -> None:
        logger.info('Initialised network analyzer...')
        self.vna = Vna()
        try:
            self.vna.open_tcp(ip_address='192.196.0.1')
        except Exception:
            logger.error('Cannot connect to VNA.')
        else:
            logger.info('Connection established.')

    def run(self, input_port = 1) -> None:
        """Measure S-Parameters for [input port]"""
        # Sweep timing handled automatically
        # Returns result:
        # 3-Dimensional numpy.ndarray:
        # [freq_point][input_port-1]
        array: numpy.ndarray = self.vna.channel(1).measure(input_port)
        array.max(axis=1)
        

        
    def stop(self) -> None:
        """Close connection."""
        self.vna.close()

