"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""
import logging
from serial import rs485
logger = logging.getLogger(__name__)

RIGHT_LIMIT = 180
LEFT_LIMIT = 270


class TurntableController(object):
    def __init__(self) -> None:
        self.turntable = rs485.RS485()
        self.turntable.rs485_mode = rs485.RS485Settings()
        logger.info('Initialised turntable.')
    
    def turn_clockwise(self, rotation: float) -> None:
        self.turntable.write()
        logger.info('turning clockwise')

    def turn_counter_clockwise(self, rotation: float) -> None:
        self.turntable.write()
        logger.info('turning counter-clockwise')

    def scan_area(self, right_limit: float = RIGHT_LIMIT, left_limit: float = LEFT_LIMIT) -> list:
        power_array: list = []
        logger.info('scanning area...')
        return power_array
    
    def find_transmitter(self) -> float:
        power_array = self.scan_area()
        max_power = max(power_array)
        logger.info(f'the maximum transmitted power measured was {max_power} at index {power_array.index(max_power)}')
        return power_array.index(max_power)
    
    def focus_beam(self, location: float, index: float) -> float:
        if location > index:
            self.turn_clockwise( (location-index) )
        if location < index:
            self.turn_counter_clockwise( (index-location) )

    def run(self) -> None:
        while True:
            location: float = 0.0
            index: float = self.find_transmitter()
            logger.info(f'Turned device {location} degrees')
            self.focus_beam(location, index)

