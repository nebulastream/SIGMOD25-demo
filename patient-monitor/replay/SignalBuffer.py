from typing import List, Tuple, Callable

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