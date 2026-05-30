from django.http import StreamingHttpResponse
import json
import queue

class SSEManager:
    def __init__(self):
        self.listeners = []

    def add_listener(self, q):
        self.listeners.append(q)

    def remove_listener(self, q):
        self.listeners.remove(q)

    def broadcast(self, data):
        for q in self.listeners:
            q.put(data)

sse_manager = SSEManager()

def sse_stream(request):
    q = queue.Queue()
    sse_manager.add_listener(q)
    def event_stream():
        try:
            while True:
                data = q.get()
                yield f"data: {json.dumps(data)}\n\n"
        except GeneratorExit:
            sse_manager.remove_listener(q)
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
