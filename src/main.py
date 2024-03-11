"""
@date: 11 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""
import logging
import threading
from turntable import TurntableController
from network_analyzer import NetworkAnalyzer

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO,
                        datefmt="%Y-%m-%d %H:%M:%S,uuu")
    
    network_analyzer = NetworkAnalyzer()
    turntable_controller = TurntableController()

    thread_turntable = threading.Thread(target=turntable_controller.run(), daemon=True)
    logging.info(f'{__file__} created thread {thread_turntable} and started it.')
    thread_network_analyzer = threading.Thread(target=network_analyzer.run(), daemon=True)
    logging.info(f'{__file__} created thread {thread_network_analyzer} and started it.')

    thread_turntable.start()
    thread_network_analyzer.start()

#https://realpython.com/intro-to-python-threading/


