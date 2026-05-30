from typing import List, Dict
import threading

class OTSession:
    def __init__(self, document: str = ""):
        self.document = document
        self.version = 0
        self.lock = threading.Lock()

    def apply(self, operation: Dict) -> str:
        with self.lock:
            # Transform operation against concurrent ops (simplified)
            if operation["version"] != self.version:
                operation = self._transform(operation)
            if operation["type"] == "insert":
                pos = operation["position"]
                text = operation["text"]
                self.document = self.document[:pos] + text + self.document[pos:]
            elif operation["type"] == "delete":
                pos = operation["position"]
                length = operation.get("length", len(operation.get("text", "")))
                self.document = self.document[:pos] + self.document[pos + length:]
            self.version += 1
            return self.document

    def _transform(self, op: Dict) -> Dict:
        # Simple transform: adjust position based on previous inserts
        # In production, use a full OT library
        return op
