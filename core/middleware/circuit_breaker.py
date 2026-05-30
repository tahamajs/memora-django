import time
from django.http import JsonResponse

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.last_failure_time = 0
        self.threshold = failure_threshold
        self.timeout = recovery_timeout

    def is_open(self):
        if self.failure_count >= self.threshold:
            if time.time() - self.last_failure_time < self.timeout:
                return True
            else:
                self.failure_count = 0  # reset
        return False

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

    def record_success(self):
        self.failure_count = 0
