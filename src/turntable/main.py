"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

from serial import rs485
from network_analyzer.main import NetworkAnalyzer

RIGHT_LIMIT = 180
LEFT_LIMIT = 270


class TurntableController():
    def __init__(self) -> None:
        self.network_analyzer = NetworkAnalyzer()
        self.turntable = rs485.RS485()
        self.turntable.rs485_mode = rs485.RS485Settings()
    
    def turn_clockwise(self, rotation: float) -> None:
        self.turntable.write()
        print('turning clockwise')

    def turn_counter_clockwise(self, rotation: float) -> None:
        self.turntable.write()
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
        self.focus_beam(location, index)

def main():
    print("Hello World!")
    turntable_controller = TurntableController()
    while True:
        turntable_controller.run()

if __name__ == "__main__":
    main()
