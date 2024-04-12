"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import logging
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

    def run(self, port) -> list:
        """Measure S-Parameters for [port]"""
        while True:
            # Measure S-Parameters for [ports]
            # Sweep timing handled automatically
            # Returns result:
            # 3-Dimensional numpy.ndarray:
            # [freq_point][output_port-1][input_port-1]
            array: list = self.vna.channel(1).measure([1,2])
        
    def stop(self) -> None:
        """Close connection."""
        self.vna.close()

