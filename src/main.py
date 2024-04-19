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

START_POS = 0.0
END_POS = 90.0
INCREASE = 10.0

lock = Lock()
cur_pos: int = 0

def run_tt_in_thread(ttc: CDispatch, ttc_id, tt_event: Event, vna_event: Event, end: Event) -> None:
    # initialize COM threading and get instance from the id and initialize turntable
    CoInitialize()
    ttc = Dispatch(CoGetInterfaceAndReleaseStream(ttc_id, IID_IDispatch))
    turntable = TurnTableController(instance="hrt i (64980128)", ttc=ttc, clockwise=True)
    
    global cur_pos # access global position variable
    count: int = 1 # counting information for logging module. Start at 1 because first position is start position

    # turn in increments
    with lock: # write current position
        cur_pos = round(turntable.position)
    while START_POS <= cur_pos < END_POS:
        tt_event.set() # signal finished turn to vna
        tt_event.clear()
        vna_event.wait() # wait for vna to signal ready
        turntable.run(INCREASE)
        with lock: # write and read current position
            cur_pos = round(turntable.position) 
            logging.info(f"Current position for {turntable.instance} is {cur_pos}.")
        count += 1
    tt_event.set()
    end.set() # indicate that all turning has finished
    logging.info(f'Turntable thread is closed. {count} positions measured.')

def run_vna_in_thread(vna: NetworkAnalyzer, tt_event: Event, vna_event: Event, end: Event) -> None:
    #tt_event.wait() # wait indefinitely for turntable to signal ready 

    global cur_pos # access global position variable
    data: list[int | list[int | float]] = [] # long data list containing [pos, [list of freq], [list of meas]] * total_pos
    count: int = 0 # counting information for logging module

    while not end.is_set(): # run only when end == false meaning stop when tt thread closes
        tt_event.wait() # wait for turntable to signal ready
        freq, pow = vna.run()
        logging.info(f'Power measurements: {pow}.')
        with lock: # read current position
            data.append(cur_pos)
            data.append(list(freq))
            data.append(list(pow))
        vna_event.set() # signal finished to turntable
        vna_event.clear()
        count += 1
    with open(f'./tests/test-{time.strftime("%Y%m%d-%H%M")}.txt', 'w') as file: # save data when turning is finished
        file.write(str(data))
    logging.info(f'VNA thread is closed. {count} measurements made.')

def main():
    logging.basicConfig(filename=f'./tests/test-{time.strftime("%Y%m%d-%H%M")}-log.txt', filemode='a',
                        format="%(asctime)s:%(name)s: %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
    
    # dispatch turntable instance and create id
    CoInitialize()
    ttc = Dispatch("TurnTableControlLib.TurnTableControl")
    ttc_id = CoMarshalInterThreadInterfaceInStream(IID_IDispatch, ttc)

    # create vna instance
    vna = NetworkAnalyzer(trace_id='tr1', s_param='s21')
    logging.info(f'VNA with trace id {vna.trace_id} is created. Measuring {vna.s_param}.')
    logging.info(f'Settings are: {vna.get_settings()}')

    # create event for syncing devices
    tt_ready = Event()
    vna_ready = Event()
    end = Event()

    # start turntable thread
    tt_thread = Thread(target=run_tt_in_thread, kwargs={'ttc_id': ttc_id, 'ttc': ttc, 'tt_event': tt_ready, 'vna_event': vna_ready, 'end': end})
    tt_thread.start()
    tt_ready.clear()

    # start VNA thread
    vna_thread = Thread(target=run_vna_in_thread, kwargs={'vna': vna, 'tt_event': tt_ready, 'vna_event': vna_ready, 'end': end})
    vna_thread.start()

    # wait until thread terminates to end main function
    tt_thread.join()
    vna_thread.join()
    
if __name__ == "__main__":
    main()