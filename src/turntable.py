"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import enum
import logging
import time
logger = logging.getLogger(__name__)

ANGLE_MIN = 0.0
ANGLE_MAX = 270.0

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

class EPolarity(enum.Enum):
    epolUnipolar = 0
    epolBipolar = 1

class TurnTableController():
    def __init__(self, instance: str, ttc, clockwise: bool = True, 
                 start_pos: float = 0.0, angle_min: float = 
                 ANGLE_MIN, angle_max: float = ANGLE_MAX) -> None:
        """ Initalize instance variables, connect and set settings."""
        self.instance = instance
        self.ttc = ttc
        self.clockwise = clockwise
        self.start_pos = start_pos
        self.angle_min = angle_min
        self.angle_max = angle_max
        if self.ttc.Count == 0:
            logger.error("No turntable is connected.")
            exit()
        elif self.connect() == EConnectionState.ecsConnectedOn.value:
            self.set(rpm=2, func=EAccelerationFunction.afImpulse, start_pos=self.start_pos)
        else:
            logger.error("Unknown error in startup sequence.")
            exit()

    def connect(self) -> int:
        """ Connect to TurnTable and check correct connection state. """
        self.tt = self.ttc.TurnTables(0)
        if self.tt.ConnectionState == EConnectionState.ecsUnconnected.value:
            logger.error("No CUD III cable is connected.")
            exit()
        elif self.tt.ConnectionState == EConnectionState.ecsConnectedOff.value:
            logger.error("The Turntable is switched off or not connected to CUD III. Try opening Turntable Control.")
            exit()
        elif self.tt.ConnectionState == EConnectionState.ecsConnectedOn.value:
            logger.info(f"Turntable {self.instance} connected.")
        return self.tt.ConnectionState
        
    def set(self, rpm: int, func: EAccelerationFunction, start_pos: float) -> None:
        """ Establish basic settings: rpm, acceleration function and start position. """
        cur_pos: int = round(self.position)
        try:
            self.tt.Velocity = rpm
            self.tt.AccelerationFunction = func.value
        except Exception as e:
            logger.error(f"Unable to set settings for turntable {self.instance}, exiting with error code {e}.")
            exit()
        if self.tt.DisplayPolarity == EPolarity.epolBipolar.value:
            try:
                self.tt.DisplayPolarity = EPolarity.epolUnipolar.value
            except Exception:
                self.angle_max = 180.0
                logger.error(f"Unable to set polarity to unipolar for turntable {self.instance}.")
        while cur_pos != round(start_pos):
            logger.info(f"Current position is {cur_pos} not start position {round(start_pos)}. Moving {self.instance} to start position.")
            if self.clockwise:
                self.go_to_CW(start_pos)
                self.wait_while_driving()
            else:
                self.go_to_CCW(start_pos)
                self.wait_while_driving()
            cur_pos = round(self.position)
        logger.info(f"Settings are velocity: {round(self.tt.Velocity)}, function: {EAccelerationFunction(self.tt.AccelerationFunction)}.")
        logger.info(f"Current position for {self.instance} is {cur_pos}.")

    def run(self, inc: float) -> None:
        """ Run the turntable. Changes the current position with [inc] degrees. """
        cur_pos: float = self.position
        if self.clockwise:
            self.step_CCW(inc)
            self.wait_while_driving()
        else:
            self.step_CW(inc)
            self.wait_while_driving()
        if (self.angle_min > cur_pos > self.angle_max):
                logger.error(f"Current position is illegal. Resetting: {self.instance}")
                self.reset(self.instance, self.clockwise)

    def reset(self, clockwise: bool = True) -> None:
        """ Reset Turntable to start position. """
        self.stop()
        if clockwise:
            self.go_to_CCW(self.start_pos)
            self.wait_while_driving()
        else:
            self.go_to_CW(self.start_pos)
            self.wait_while_driving()

    def stop(self) -> None:
        """ Stop turning. """
        if self.tt.IsMoving:
            self.tt.MoveAbort()
            logger.warning(f"Turntable was moving while connection was stopped for {self.instance}.")
        logger.info(f"Turntable {self.instance} is stopped.")

    def wait_while_driving(self) -> None:
        """ Ensures that the program waits for the turntable to reach position before execution further code. """
        seconds_waited = 0.0
        while self.tt.IsMoving:
            time.sleep(0.5)
            seconds_waited += 0.5
            if seconds_waited > 120:
                print('Timeout while waiting for turntable to stop')
                break

    def step_CW(self, degrees, wait: bool = True) -> None:
        """ Step [degrees] in clockwise direction. """
        self.tt.StepSize = float(degrees)
        self.tt.StepCW()
        if wait:
            self.wait_while_driving()

    def step_CCW(self, degrees: float, wait: bool = True) -> None:
        """ Step [degrees] in counter-clockwise direction. """
        self.tt.StepSize = float(degrees)
        self.tt.StepCCW()
        if wait:
            self.wait_while_driving()

    def go_to_CW(self, degrees: float, wait: bool = True) -> None:
        """ Go to [degrees] while moving in clockwise direction. """
        self.tt.GotoCW(float(degrees))
        if wait:
            self.wait_while_driving()

    def go_to_CCW(self, degrees: float, wait: bool = True) -> None:
        """ Go to [degrees] while moving in counter-clockwise direction. """
        self.tt.GotoCCW(degrees)
        if wait:
            self.wait_while_driving()

    @property
    def position(self):
        return self.tt.Position
