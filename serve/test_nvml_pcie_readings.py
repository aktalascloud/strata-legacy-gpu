"""NVML counter handling with fake driver answers; no GPU, clocks or OS calls."""
import unittest
from serve import telemetry


class NvmlPcieReadings(unittest.TestCase):
    def read(self, answers, counter=1):
        class Lib:
            def nvmlDeviceGetPcieThroughput(self, dev, which, output):
                calls.append(which.value)
                value = left.pop(0)
                if value is None: return 1
                output._obj.value = value
                return 0
        left, calls = list(answers), []
        gpu = telemetry._Nvml.__new__(telemetry._Nvml)
        gpu.dev, gpu.lib = None, Lib()
        return gpu._pcie_mb(counter), calls, left

    def test_supported_readings_unchanged_and_unsupported_not_retried(self):
        for value in (0, 2048, 58 << 20, telemetry.PCIE_KB_S_MAX):
            self.assertEqual(self.read([value, 1]), (value / 1024.0, [1], [1]))
        self.assertEqual(self.read([None, 2048]), (None, [1], [2048]))

    def test_wrap_retries_exact_same_counter_once(self):
        for counter in (0, 1):
            self.assertEqual(self.read([209708000, 2048], counter), (2.0, [counter, counter], []))

    def test_repeated_wrap_or_failed_retry_is_unreadable(self):
        for second in (209708000, None):
            self.assertEqual(self.read([209708000, second, 2048]), (None, [1, 1], [2048]))


if __name__ == '__main__': unittest.main()
