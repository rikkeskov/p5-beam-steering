"""
@date: 11 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import logging
import time
from threading import Thread, Event, Lock
from pythoncom import CoInitialize, CoGetInterfaceAndReleaseStream, CoMarshalInterThreadInterfaceInStream, IID_IDispatch
from win32com.client import Dispatch, CDispatch
from network_analyzer import NetworkAnalyzer
from turntable import TurnTableController

START_POS = 10.0
END_POS = 150.0
INCREASE = 20.0

lock_cur_pos = Lock()
cur_pos: int = None

max_pos_event_handler = Event()
lock_max_pos = Lock()
max_pos: int = None

def run_tt_in_thread(ttc: CDispatch, turntable_event_handler: Event, vna_event_handler: Event, end: Event, ttc_id) -> None:
    CoInitialize()
    ttc = Dispatch(CoGetInterfaceAndReleaseStream(ttc_id, IID_IDispatch))
    turntable = TurnTableController(instance="hrt i (64980128)", ttc=ttc, clockwise=True, start_pos=START_POS)
    
    global cur_pos
    global max_pos
    count: int = 1

    with lock_cur_pos:
        cur_pos = round(turntable.position)

    while START_POS <= cur_pos < END_POS:
        turntable_event_handler.set()
        turntable_event_handler.clear()
        vna_event_handler.wait()
        turntable.run(INCREASE)
        with lock_cur_pos:
            cur_pos = round(turntable.position) 
            logging.info(f"Current position for {turntable.instance} is {cur_pos}.")
        count += 1
    turntable_event_handler.set()
    turntable_event_handler.clear()
    end.set()

    max_pos_event_handler.wait()
    with lock_max_pos:
        if turntable.clockwise:
            turntable.go_to_CW(max_pos)
        else:
            turntable.go_to_CCW(max_pos)

    logging.info(f'Turntable thread is closed. {count} positions measured.')

def run_vna_in_thread(vna: NetworkAnalyzer, turntable_event_handler: Event, vna_event_handler: Event, end: Event) -> None:
    global cur_pos 
    global max_pos
    data_pos: list = []
    data_pow: list = []
    count: int = 0 

    while not end.is_set(): # run only when end == false
        turntable_event_handler.wait() 
        _, pow = vna.run()
        vna_event_handler.set() 
        vna_event_handler.clear()
        logging.info(f'Power measurement is {pow}.')
        with lock_cur_pos: 
            data_pos.append(cur_pos)
            data_pow.append(pow)
        count += 1
    max_gain: float = max(data_pow)
    with lock_max_pos:
        max_pos = data_pos[data_pow.index(max_gain)]
    logging.info(f'Max gain measured is {max_gain} at position {max_pos}.')
    max_pos_event_handler.set() 

    logging.info(f'VNA thread is closed. {count} measurements made.')

def main():
    logging.basicConfig(filename=f'./tests/test-{time.strftime("%Y%m%d-%H%M")}-log.txt', filemode='a', format="%(asctime)s:%(name)s: %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
    
    CoInitialize()
    ttc = Dispatch("TurnTableControlLib.TurnTableControl")
    ttc_id = CoMarshalInterThreadInterfaceInStream(IID_IDispatch, ttc)
    
    vna = NetworkAnalyzer(trace_id='trc1', s_param='s21', freq=5.65)
    vna.vna_set()
    logging.info(f'VNA with trace id {vna.trace_id} is created. Measuring {vna.s_param}.')
    logging.info(f'Settings are: {vna.get_settings()}')

    turntable_event_handler = Event()
    vna_event_handler_handler = Event()
    end = Event()
    turntable_thread = Thread(target=run_tt_in_thread, kwargs={'ttc_id': ttc_id, 'ttc': ttc, 'turntable_event_handler': turntable_event_handler, 'vna_event_handler': vna_event_handler_handler, 'end': end})

    turntable_event_handler.clear()
    vna_thread = Thread(target=run_vna_in_thread, kwargs={'vna': vna, 'turntable_event_handler': turntable_event_handler, 'vna_event_handler': vna_event_handler_handler, 'end': end})
    
    turntable_thread.start()
    vna_thread.start()

    turntable_thread.join()
    vna_thread.join()
    
if __name__ == "__main__":
    main()