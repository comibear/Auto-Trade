# src/layers/trigger/TimeBased.py
# Time based trigger layer

import threading
import time

class TimeBasedTrigger:
    """
    A system to trigger an action at a regular time interval.
    """

    def __init__(self, interval_seconds, action):
        """
        :param interval_seconds: Time between triggers, in seconds
        :param action: Callable (function) to execute every interval
        """
        self.interval_seconds = interval_seconds
        self.action = action
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True

    def _run(self):
        while not self._stop_event.is_set():
            self.action()
            time.sleep(self.interval_seconds)

    def start(self):
        """
        Start the time-based trigger.
        """
        self._stop_event.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run)
            self._thread.daemon = True
            self._thread.start()

    def stop(self):
        """
        Stop the time-based trigger.
        """
        self._stop_event.set()
        self._thread.join()

if __name__ == "__main__":
    # Example usage:
    # def tick():
    #     print("Tick at:", time.strftime("%X"))

    # tb = TimeBasedTrigger(5, tick)
    # tb.start()
    # time.sleep(20)
    # tb.stop()
    
    pass