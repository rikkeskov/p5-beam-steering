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








"""import enum
import threading
import pythoncom
from win32com.client import DispatchWithEvents, gencache, getevents, _event_setattr_, EventsProxy

# AccelerationFunction Constants
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

# decorator for improved handling of COM-Exceptions
def ExceptionDecorator(func):
    def y(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pythoncom.com_error as err:
            raise RuntimeError(err.excepinfo[2])
    return y

# event support
class TurnTableControlEvents(object):
    def OnUSBConnected(self, FTDISerialNumber: str):
        print("[TurnTableControlEvents.OnUSBConnected] %s" % FTDISerialNumber)

    def OnUSBDisconnected(self, FTDISerialNumber: str):
        print("[TurnTableControlEvents.OnUSBDisconnected] %s" % FTDISerialNumber)

    def OnError(self, Msg: str):
        print("[TurnTableControlEvents.OnError] %s" % Msg)

class TurnTableEvents(object):
    def __init__(self, movingEventStart, movingEventStop):
        self.movingEventStart = movingEventStart
        self.movingEventStop = movingEventStop

    def OnError(self, Msg: str):
        print("[TurnTableEvents.OnError] %s" % Msg)

    def OnNewPosition(self, NewPosition: float):
        print("[TurnTableEvents.OnNewPosition] %.2f" % (NewPosition))

    def OnConnectionStateChanged(self, State: int):
        State = EConnectionState(State)
        print("[TurnTableEvents.OnConnectionStateChanged] %s" % (State.name))

    def OnHRTStateChanged(self, newState: int):
        newState = ETurnTableState(newState)
        if newState == ETurnTableState.ettsStarted:
            self.movingEventStart.set()
            self.movingEventStop.clear()
        elif newState == ETurnTableState.ettsStopped:
            self.movingEventStop.set()
            self.movingEventStart.clear()

        print("[TurnTableEvents.OnHRTStateChanged] %s" % (newState.name))

# turntable class
class TurnTable(object):
    # Helper function to generate event support
    @staticmethod
    def __getEventInstance(comObj, progId, user_event_class, *user_event_class_args, **user_event_class_kwargs):
        disp_class = gencache.GetClassForProgID(progId)
        clsid = disp_class.CLSID
        events_class = getevents(clsid)
        result_class = type("COMEventClass", (disp_class, user_event_class),
                            {"__setattr__": _event_setattr_})
        instance = result_class(comObj._oleobj_)  # This only calls the first base class __init__.
        inst_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, instance)
        events_class.__init__(instance, instance)
        user_event_class.__init__(instance, *user_event_class_args, **user_event_class_kwargs)
        return EventsProxy(instance)

    def __init__(self, TTControl=None, ttIndex=0, waitDrivingTimeOutSeconds=120, waitStartDrivingTimeOutSeconds=8.0, stopIfDriving=True, **kwargs):
        # timeout definitions
        self.waitDrivingTimeOutSeconds = waitDrivingTimeOutSeconds
        self.waitStartDrivingTimeOutSeconds = waitStartDrivingTimeOutSeconds
        self._pumpMessageTime = kwargs.get('pumpMessageTime', 0.050)

        # get turntable object with event support
        if TTControl is None:
            self.__TTControl = DispatchWithEvents("TurnTableControlLib.TurnTableControl", TurnTableControlEvents)
        else:
            self.__TTControl = TTControl

        # set events for non-blocking waiting operations
        print("Number of Turntables found: %d" % self.__TTControl.Count)
        if self.__TTControl.Count > ttIndex:
            # initialize: stop = active, start = inactive
            self.movingEventStart = threading.Event()
            self.movingEventStart.clear()

            self.movingEventStop = threading.Event()
            self.movingEventStop.set()

            # Turntable object with event support
            self.__TT = self.__getEventInstance(self.__TTControl.TurnTables(ttIndex), "TurnTableControlLib.TurnTable",
                                                TurnTableEvents, self.movingEventStart, self.movingEventStop)

            if stopIfDriving and self.GetIsMoving():
                self.MoveAbort()
        else:
            raise Exception('No Turntable found for index %d' % ttIndex)

    def WaitWhileDriving(self, raiseExceptionOnTimeOut=True):
        # wait for start/stop driving...
        waitResult = True
        for eventName, event, waitTimeOut in zip(['start', 'stop'],
                                                 [self.movingEventStart, self.movingEventStop],
                                                 [self.waitStartDrivingTimeOutSeconds, self.waitDrivingTimeOutSeconds]):

            maxNbrLoops = round(waitTimeOut / self._pumpMessageTime)
            nbrLoops = 0
            while nbrLoops < maxNbrLoops:
                pythoncom.PumpWaitingMessages()
                if not event.wait(self._pumpMessageTime):
                    nbrLoops += 1
                else:
                    break

            # check for successful wait:
            waitResult = nbrLoops > 0
            if raiseExceptionOnTimeOut and not waitResult:
                raise Exception(f'Timeout while wait for turntable to {eventName}')

        return waitResult

    @ExceptionDecorator
    def StepCW(self, Degrees, WaitWhileDriving:bool=True):
        self.__TT.StepSize = float(Degrees)
        self.__TT.StepCW()
        if WaitWhileDriving:
            self.WaitWhileDriving()

    @ExceptionDecorator
    def StepCCW(self, Degrees: float, WaitWhileDriving:bool=True):
        self.__TT.StepSize = float(Degrees)
        self.__TT.StepCCW()
        if WaitWhileDriving:
            self.WaitWhileDriving()

    @ExceptionDecorator
    def GotoCW(self, Degrees: float, WaitWhileDriving:bool=True):
        self.__TT.GotoCW(float(Degrees))
        if WaitWhileDriving:
            self.WaitWhileDriving()

    @ExceptionDecorator
    def GotoCCW(self, Degrees: float, WaitWhileDriving:bool=True):
        self.__TT.GotoCCW(Degrees)
        if WaitWhileDriving:
            self.WaitWhileDriving()

    @ExceptionDecorator
    def GetPosition(self) -> float:
        return self.__TT.Position

    @ExceptionDecorator
    def GotoPosition(self, Position: float, WaitWhileDriving:bool=True):
        self.__TT.GotoPosition(Position)
        if WaitWhileDriving:
            self.WaitWhileDriving()

    @ExceptionDecorator
    def SetAsOrigin(self):
        self.__TT.SetOrigin()

    @ExceptionDecorator
    def MoveAbort(self):
        self.__TT.MoveAbort()

    @ExceptionDecorator
    def ResetStepSum(self):
        self.__TT.ResetStepSum()

    @ExceptionDecorator
    def GetIsMoving(self) -> bool:
        return self.__TT.IsMoving

    @ExceptionDecorator
    def GetSummedUpSteps(self) -> float:
        return self.__TT.SummedUpSteps

    @ExceptionDecorator
    def GetAccelerationFunction(self) -> EAccelerationFunction:
        return EAccelerationFunction(self.__TT.AccelerationFunction)

    @ExceptionDecorator
    def SetAccelerationFunction(self, Val: EAccelerationFunction):
        Val = EAccelerationFunction(Val)
        self.__TT.AccelerationFunction = int(Val.value)

    @ExceptionDecorator
    def GetVelocity(self) -> float:
        return self.__TT.Velocity

    @ExceptionDecorator
    def SetVelocity(self, Val: float):
        self.__TT.Velocity = Val"""