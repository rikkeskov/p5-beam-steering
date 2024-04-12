"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import enum
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
class TurnTableControlEvents:
    def OnUSBConnected(self, FTDISerialNumber: str):
        print("[TurnTableControlEvents.OnUSBConnected] %s" % FTDISerialNumber)

    def OnUSBDisconnected(self, FTDISerialNumber: str):
        print("[TurnTableControlEvents.OnUSBDisconnected] %s" % FTDISerialNumber)

    def OnError(self, Msg: str):
        print("[TurnTableControlEvents.OnError] %s" % Msg)

class TurnTableEvents:
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

class TurnTable:
    # Helper function to generate event support
    @staticmethod
    def __getEventInstance(comObj, progId, user_event_class, *user_event_class_args, **user_event_class_kwargs):
        disp_class = gencache.GetClassForProgID(progId)
        clsid = disp_class.CLSID
        events_class = getevents(clsid)
        print(type(disp_class))
        print(type(events_class))
        print(type(user_event_class))
        result_class = type("COMEventClass", (disp_class, events_class, user_event_class),
                            {"__setattr__": _event_setattr_})
        instance = result_class(comObj._oleobj_)  # This only calls the first base class __init__.
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

            if stopIfDriving and self.IsMoving:
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
                raise Exception('Timeout while wait for turntable to %s' % eventName)

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
    def GotoPosition(self, Position: float, WaitWhileDriving:bool=True):
        self.__TT.GotoPosition(Position)
        if WaitWhileDriving:
            self.WaitWhileDriving()

    @ExceptionDecorator
    def GetPosition(self) -> float:
        return self.__TT.Position

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
        self.__TT.Velocity = Val

    # Properties
    AccelerationFunction = property(GetAccelerationFunction, SetAccelerationFunction)
    Position = property(GetPosition, GotoPosition)
    Velocity = property(GetVelocity, SetVelocity)
    IsMoving = property(GetIsMoving)

if __name__ == "__main__":
    tt = TurnTable()
