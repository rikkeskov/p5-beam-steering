"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import usb.core
import usb.util
from network_analyzer.main import NetworkAnalyzer

RIGHT_LIMIT = 180
LEFT_LIMIT = 270


class TurntableController():
    def __init__(self, device) -> None:
        self.device = device
        self.network_analyzer = NetworkAnalyzer()

    def establish_connection(self) -> None:
        self.device = usb.core.find()
        if self.device is None:
            raise ValueError('Device not found')
        else:
            self.device.set_configuration()
    
    def turn_clockwise(self, rotation: float) -> None:
        print('turning clockwise')

    def turn_counter_clockwise(self, rotation: float) -> None:
        print('turning counter-clockwise')

    def scan_area(self, right_limit: float = RIGHT_LIMIT, left_limit: float = LEFT_LIMIT) -> list:
        power_array: list = []
        print('scanning area...')
        analysis = self.network_analyzer.run()
        return power_array
    
    def find_transmitter(self) -> float:
        power_array = self.scan_area()
        max_power = max(power_array)
        print(f'the maximum transmitted power measured was {max_power} at index {power_array.index(max_power)}')
        return power_array.index(max_power)
    
    def focus_beam(self, location: float, index: float) -> float:
        if location > index:
            self.turn_clockwise( (location-index) )
        if location < index:
            self.turn_counter_clockwise( (index-location) )

    def run(self) -> None:
        location: float = 0.0
        index: float = self.find_transmitter()
        self.focus_beam( location, index)

def main():
    print("Hello World!")
    turntable_controller = TurntableController()
    while True:
        turntable_controller.run()

if __name__ == "__main__":
    main()
