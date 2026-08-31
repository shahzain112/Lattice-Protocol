import threading
import queue
import time

class AgentSwarm:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.results = []
    
    def add_task(self, task_name: str, data: dict):
        self.task_queue.put((task_name, data))
    
    def run_swarm(self, num_workers=5):
        def worker():
            while not self.task_queue.empty():
                task, data = self.task_queue.get()
                # Simulate AI work (Replace with actual LLM calls later)
                result = f"Processed {task} with data: {data}"
                self.results.append(result)
                time.sleep(0.1)  # Simulate processing time
                self.task_queue.task_done()
        
        threads = [threading.Thread(target=worker) for _ in range(num_workers)]
        for t in threads: t.start()
        for t in threads: t.join()
        
        return self.results