"""
@date: 11 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import enum
import logging
import pythoncom
import threading
import time
from win32com.client import Dispatch
from network_analyzer import NetworkAnalyzer

ANGLE_MIN = 0.0
ANGLE_MAX = 270.0

def run_in_thread(ttc, ttc_id):
    # initialize
    pythoncom.CoInitialize()
    start_pos: float = 0.0
    end_pos: float = 270.0
    angle_min: float = ANGLE_MIN
    angle_max: float = ANGLE_MAX

    # get instance from the id
    ttc = Dispatch(pythoncom.CoGetInterfaceAndReleaseStream(ttc_id, pythoncom.IID_IDispatch))

    # initialize to start position
    turntable = TurnTableController("hrt i 2", ttc=ttc)
    cur_pos: float = turntable.position
    
    # turn in increments
    while start_pos <= cur_pos < end_pos:
        turntable.run(inc = 10.0)
        cur_pos = turntable.position

        if (angle_min > cur_pos > angle_max):
                logging.error(f"Current position is illegal. Resetting: {turntable.instance}")
                turntable.reset(turntable.instance, turntable.clockwise)

class EAccelerationFunction(enum.Enum):
    afImpulse = 0
    afSteep = 5
    afMedium = 6
    afFlat = 7

class EConnectionState(enum.Enum):
    ecsUnconnected = 0
    ecsConnectedOff = 1
    ecsConnectedOn = 2

class ETurnTableState(enum.Enum):
    ettsStarted = 0
    ettsStopped = 1
    ettsAllowedAngleReached = 2

class TurnTableController():
    def __init__(self, instance: str, ttc, clockwise: bool = True, start_pos: float = 0.0):
        """ Initalize instance variables, connect and set settings."""
        self.instance = instance
        self.ttc = ttc
        self.clockwise = clockwise
        self.start_pos = start_pos

        if self.ttc.Count == 0:
            logging.error("No turntable is connected.")
            exit()
        elif self.connect() == EConnectionState.ecsConnectedOn.value:
            self.set(rpm=2, func=EAccelerationFunction.afFlat, start_pos=self.start_pos)

    def connect(self) -> int:
        """ Connect to TurnTable and check correct connection state. """
        self.tt = self.ttc.TurnTables(0)
        if self.tt.ConnectionState == EConnectionState.ecsUnconnected.value:
            logging.error("No CUD III cable is connected.")
            exit()
        elif self.tt.ConnectionState == EConnectionState.ecsConnectedOff.value:
            logging.error("The Turntable is switched off or not connected to CUD III. Try opening Turntable Control.")
            exit()
        elif self.tt.ConnectionState == EConnectionState.ecsConnectedOn.value:
            logging.info(f"Turntable {self.instance} connected.")
        return self.tt.connectionState
        
    def set(self, rpm: int, func: EAccelerationFunction, start_pos: float):
        """ Establish basic settings: rpm, acceleration function and start position. """
        cur_pos: float = self.position
        try:
            self.tt.Velocity = rpm
            self.tt.AccelerationFunction = func.value
        except Exception as e:
            logging.error(f"Unable to set settings for turntable {self.instance}, exiting with error code {e}.")
            exit()

        while cur_pos != start_pos:
            logging.info(f"Current position is {cur_pos} not start position {start_pos}. Moving {self.instance} to start position.")
            if self.clockwise:
                self.go_to_CW(start_pos)
                self.wait_while_driving()
            else:
                self.go_to_CCW(start_pos)
                self.wait_while_driving()
                cur_pos = self.position
        
        logging.info(f"Settings are: [velocity: {self.tt.Velocity}, function: {self.tt.AccelerationFunction}, position: {self.position}].")

    def run(self, inc: float):
        """ Run the turntable. Changes the current position with [inc] degrees. """
        cur_pos: float = self.position

        if self.clockwise:
            self.step_CCW(inc)
            self.wait_while_driving()
        else:
            self.step_CW(inc)
            self.wait_while_driving()
        logging.info(f"loc 114: Current position is {cur_pos}.")

    def reset(self, clockwise: bool = True):
        """ Reset Turntable to start position. """
        self.stop()
        
        if clockwise:
            self.go_to_CCW(self.start_pos)
            self.wait_while_driving()
        else:
            self.go_to_CW(self.start_pos)
            self.wait_while_driving()

    def stop(self):
        """ Stop turning. """
        if self.tt.IsMoving:
            self.tt.MoveAbort()
            logging.warning(f"Turntable was moving while connection was stopped for {self.instance}.")

        logging.info(f"Turntable {self.instance} is stopped.")

    def wait_while_driving(self):
        """ Ensures that the program waits for the turntable to reach position before execution further code. """
        seconds_waited = 0.0
        while self.tt.IsMoving:
            time.sleep(0.5)
            seconds_waited += 0.5
            if seconds_waited > 120:
                print('Timeout while waiting for turntable to stop')
                break

    def step_CW(self, degrees, wait: bool = True):
        """ Step [degrees] in clockwise direction. """
        self.tt.StepSize = float(degrees)
        self.tt.StepCW()
        if wait:
            self.wait_while_driving()

    def step_CCW(self, degrees: float, wait: bool = True):
        """ Step [degrees] in counter-clockwise direction. """
        self.tt.StepSize = float(degrees)
        self.tt.StepCCW()
        if wait:
            self.wait_while_driving()

    def go_to_CW(self, degrees: float, wait: bool = True):
        """ Go to [degrees] while moving in clockwise direction. """
        self.tt.GotoCW(float(degrees))
        if wait:
            self.wait_while_driving()

    def go_to_CCW(self, degrees: float, wait: bool = True):
        """ Go to [degrees] while moving in counter-clockwise direction. """
        self.tt.GotoCCW(degrees)
        if wait:
            self.wait_while_driving()

    @property
    def position(self):
        return self.tt.Position

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO,
                        datefmt="%Y-%m-%d %H:%M:%S")
    pythoncom.CoInitialize()
    #vna = NetworkAnalyzer()
    
    # dispatch turntable instance and create id
    ttc = Dispatch("TurnTableControlLib.TurnTableControl")
    ttc_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, ttc)

    # start turntable thread https://realpython.com/intro-to-python-threading/
    tt_thread = threading.Thread(target=run_in_thread, kwargs={'ttc_id': ttc_id, 'ttc': ttc} )
    tt_thread.start()

    tt_thread.join()


