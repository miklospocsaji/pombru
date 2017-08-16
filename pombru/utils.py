"Various general purpose utilities."
import logging
import time
import threading

def enum(*args):
    """Creates an enumeration from the parameter values.
    All parameters must be strings which are valid python identifiers
    """
    values = {x: i for i, x in enumerate(args)}
    return type("Enum", (), values)

class PausableTimer(object):
    """Timer which can be paused and resumed if not already fired.
    The callback will receive the timer instance before all the other parameters."""

    State = enum('CREATED', 'STARTED', 'PAUSED', 'CANCELLED', 'FINISHED')

    def __init__(self, timeout, callback, name=None, *args, **kwargs):
        self._timer = threading.Timer(timeout, self._callback_wrapper, args, kwargs)
        self._orig_timeout = timeout
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self._state = PausableTimer.State.CREATED
        self._started_at = None
        self._paused_at = None
        self._lock = threading.RLock()
        self.name = name

    def _callback_wrapper(self, *args, **kwargs):
        start = False
        with self._lock:
            if self._state == PausableTimer.State.STARTED:
                self._state = PausableTimer.State.FINISHED
                start = True
        if start:
            self._callback(self, *self._args, **self._kwargs)

    def start(self):
        if self._state != PausableTimer.State.CREATED:
            raise RuntimeError("Timer's state is " + self._state)
        self._state = PausableTimer.State.STARTED
        self._started_at = time.time()
        self._timer.start()
        logging.debug("Timer " + str(self.name) + " with timeout " + str(self._orig_timeout) + " started.")

    def cancel(self):
        with self._lock:
            if self._state != PausableTimer.State.FINISHED and self._state != PausableTimer.State.CANCELLED:
                self._state = PausableTimer.State.CANCELLED
                self._timer.cancel()

    def pause(self):
        with self._lock:
            if (self._state == PausableTimer.State.STARTED):
                now = time.time()
                if now - self._started_at < self._orig_timeout:
                    self._state = PausableTimer.State.PAUSED
                    self._paused_at = now
                    self._timer.cancel()
                    self._timer = None

    def resume(self):
        with self._lock:
            if self._state == PausableTimer.State.PAUSED:
                new_timeout = self._orig_timeout - (self._paused_at - self._started_at)
                self._timer = threading.Timer(new_timeout, self._callback, self._args, self._kwargs)
                self._state = PausableTimer.State.STARTED
                self._timer.start()

    def get_state(self):
        return self._state

    def remaining(self):
        with self._lock:
            if self._state == PausableTimer.State.STARTED:
                return self._orig_timeout - (time.time() - self._started_at)
            elif self._state == PausableTimer.State.PAUSED:
                return self._orig_timeout - (self._paused_at - self._started_at)
            else:
                return -1

    def __str__(self):
        return "[PausableTimer: " + str(self.name) + ", timeout: " + str(self._orig_timeout) + "]"

    def __repr__(self):
        return self.__str__()

if __name__ == "__main__":
    def callback():
        print "callback!"
    rt = PausableTimer(5, callback)
    sec = 0
    def pause():
        rt.pause()
        print "paused"
    def resume():
        rt.resume()
        print "resumed"
    def onesec():
        threading.Timer(1, onesec).start()
        global sec
        if sec == 2:
            pause()
        if sec == 14:
            resume()
        print sec
        sec += 1
    rt.start()
    onesec()
