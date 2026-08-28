import time
from typing import List, Tuple, Callable
import threading
import math

class SignalBuffer:
    def __init__(self, values, indices):
        self.values = values
        self.indices = indices

    @staticmethod
    def precompute(count: int, func: Callable[[int], List[float]]) -> 'SignalBuffer':
        indices = []
        values = []
        for i in range(count):
            indices.append(len(values))
            values.extend(func(i))
        indices.append(len(values))

        return SignalBuffer(values, indices)

    def get_signal(self, index: int, theta: float) -> float:
        start = self.indices[index]
        end = self.indices[index + 1]
        length = end - start
        i = int(start + length * theta)
        return self.values[i]

class PeriodicSignalHandler:
    def __init__(self, signal_buffer: SignalBuffer):
        self.signal_buffer = signal_buffer
        self._queue = [{"index": 0, "duration": 1000}]
        self._current_start = time.time()

    def next_index(self, index: int, duration: int):
        next_item = {"index": index, "duration": duration}
        if len(self._queue) < 2:
            self._queue.append(next_item)
        else:
            self._queue[-1] = next_item

    def reset_signal(self):
        if len(self._queue) > 1:
            self._queue.pop(0)
        self._current_start = time.time()

    def get_theta(self) -> float:
        theta = (time.time() - self._current_start) / self._queue[0]["duration"]
        if theta > 1:
            self.reset_signal()
            return 0
        return theta

    def get_signal(self) -> float:
        theta = self.get_theta()
        current = self._queue[0]
        next_item = self._queue[1] if len(self._queue) > 1 else current

        transition_width = 0.15
        transition = smoothstep(1.0 - transition_width, 1.0, theta)

        s = lerp(
            self.signal_buffer.get_signal(current["index"], theta),
            self.signal_buffer.get_signal(next_item["index"], 1 - theta),
            transition
        )
        return s

def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smoothstep function for smooth interpolation."""
    x = max(0, min(1, (x - edge0) / (edge1 - edge0)))
    return x * x * (3 - 2 * x)

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + t * (b - a)

# Example usage
def example_func(i: int) -> List[float]:
    return [float(i), float(i + 1), float(i + 2)]

signal_buffer = SignalBuffer.precompute(5, example_func)
handler = PeriodicSignalHandler(signal_buffer)

# Get a signal value
print(handler.get_signal())

# Helper functions
def remap(value: float, low1: float, high1: float, low2: float, high2: float) -> float:
    return low2 + (value - low1) * (high2 - low2) / (high1 - low1)

def generate_signal(frequency: float, duration: float = 1.0, sample_rate: int = 44100) -> List[float]:
    """Generate a sine wave signal."""
    return [0.5 * math.sin(2 * math.pi * frequency * i / sample_rate) + 0.5
            for i in range(int(sample_rate * duration))]

def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smoothstep function for smooth interpolation."""
    x = max(0, min(1, (x - edge0) / (edge1 - edge0)))
    return x * x * (3 - 2 * x)

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + t * (b - a)

# SignalBuffer class
class SignalBuffer:
    def __init__(self, values: List[float], indices: List[int]):
        self.values = values
        self.indices = indices

    @staticmethod
    def precompute(count: int, func: Callable[[int], List[float]]) -> 'SignalBuffer':
        indices = []
        values = []
        for i in range(count):
            indices.append(len(values))
            values.extend(func(i))
        indices.append(len(values))
        return SignalBuffer(values, indices)

    def get_signal(self, index: int, theta: float) -> float:
        start = self.indices[index]
        end = self.indices[index + 1]
        length = end - start
        i = int(start + length * theta)
        return self.values[i]

# PeriodicSignalHandler class
class PeriodicSignalHandler:
    def __init__(self, signal_buffer: SignalBuffer):
        self.signal_buffer = signal_buffer
        self._queue = [{"index": 0, "duration": 1000}]
        self._current_start = time.time()

    def next_index(self, index: int, duration: int):
        next_item = {"index": index, "duration": duration}
        if len(self._queue) < 2:
            self._queue.append(next_item)
        else:
            self._queue[-1] = next_item

    def reset_signal(self):
        if len(self._queue) > 1:
            self._queue.pop(0)
        self._current_start = time.time()

    def get_theta(self) -> float:
        theta = (time.time() - self._current_start) / (self._queue[0]["duration"] / 1000)
        if theta > 1:
            self.reset_signal()
            return 0
        return theta

    def get_signal(self) -> float:
        theta = self.get_theta()
        current = self._queue[0]
        next_item = self._queue[1] if len(self._queue) > 1 else current

        transition_width = 0.15
        transition = smoothstep(1.0 - transition_width, 1.0, theta)

        s = lerp(
            self.signal_buffer.get_signal(current["index"], theta),
            self.signal_buffer.get_signal(next_item["index"], 1 - theta),
            transition
        )
        return s

# Scheduler class
class Scheduler:
    def __init__(self, callback: Callable[[float, float], None]):
        self.callback = callback
        self.last_rr_ms = 1000  # Default 1 second
        self.running = False
        self.thread = None

    def reset(self):
        self.last_rr_ms = 1000

    def update(self):
        # In a real implementation, this would calculate the actual RR interval
        # For this example, we'll just keep it constant
        pass

    def get_last_rr_ms(self) -> float:
        return self.last_rr_ms

    def start(self, interval_ms: int = 50):
        self.running = True
        self.thread = threading.Thread(target=self._run, args=(interval_ms,))
        self.thread.start()

    def _run(self, interval_ms: int):
        while self.running:
            start_time = time.time()
            self.callback(time.time(), self.last_rr_ms)
            elapsed = (time.time() - start_time) * 1000
            sleep_time = max(0, interval_ms - elapsed) / 1000
            time.sleep(sleep_time)

# Main test function
def main():
    count = 20
    min_freq = 20
    max_freq = 120
    update_width = 0.5

    # Create signal buffer
    signal_buffer = SignalBuffer.precompute(
        count,
        lambda i: generate_signal(remap(i, 0, count - 1, min_freq, max_freq))
    )

    # Create signal handler
    signal_handler = PeriodicSignalHandler(signal_buffer)

    # Create scheduler
    scheduler = Scheduler(lambda ts, rr_ms: signal_handler.next_index(0, rr_ms))
    scheduler.start(50)  # Update every 50ms

    # Initialize variables
    pre_update = True
    signal_handler.reset_signal()
    scheduler.reset()

    # Main loop
    try:
        last_update_time = time.time()
        while True:
            current_time = time.time()
            if current_time - last_update_time >= 0.01:  # 10ms interval
                signal = signal_handler.get_signal()
                theta = signal_handler.get_theta()

                if theta < update_width:
                    pre_update = True
                elif pre_update:
                    bpm = 60000 / scheduler.get_last_rr_ms()
                    print(f"Current BPM: {bpm:.1f}, Signal: {signal:.4f}, Theta: {theta:.4f}")
                    pre_update = False

                last_update_time = current_time

            time.sleep(0.001)  # Small sleep to prevent CPU overload

    except KeyboardInterrupt:
        print("\nStopping...")
        scheduler.running = False
        scheduler.thread.join()

if __name__ == "__main__":
    main()