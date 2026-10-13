import redis
import json
import uuid
import time
import threading
import signal
import sys
from datetime import datetime

class TaskQueue:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(host=host, port=port, db=db)
        self.queue_name = 'task_queue'
        self.result_prefix = 'task_result:'
        self.scheduled_prefix = 'scheduled_tasks'
    
    def enqueue(self, task_type, payload, priority=0, delay=0):
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'type': task_type,
            'payload': payload,
            'priority': priority,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        if delay > 0:
            # Scheduled task
            execute_at = time.time() + delay
            self.redis_client.zadd(self.scheduled_prefix, {json.dumps(task): execute_at})
        else:
            # Immediate task
            self.redis_client.lpush(self.queue_name, json.dumps(task))
        
        self.redis_client.set(f"{self.result_prefix}{task_id}", json.dumps({'status': 'pending'}))
        return task_id
    
    def dequeue(self):
        # Check for scheduled tasks first
        now = time.time()
        scheduled = self.redis_client.zrangebyscore(self.scheduled_prefix, 0, now)
        if scheduled:
            for task_json in scheduled:
                if self.redis_client.zrem(self.scheduled_prefix, task_json):
                    self.redis_client.rpush(self.queue_name, task_json)
        
        # Get task from queue (blocking pop with timeout)
        result = self.redis_client.brpop(self.queue_name, timeout=1)
        if result:
            return json.loads(result[1])
        return None
    
    def complete_task(self, task_id, result):
        task_result = {
            'status': 'completed',
            'result': result,
            'completed_at': datetime.now().isoformat()
        }
        self.redis_client.set(f"{self.result_prefix}{task_id}", json.dumps(task_result))
    
    def fail_task(self, task_id, error):
        task_result = {
            'status': 'failed',
            'error': str(error),
            'failed_at': datetime.now().isoformat()
        }
        self.redis_client.set(f"{self.result_prefix}{task_id}", json.dumps(task_result))
    
    def get_result(self, task_id, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            result = self.redis_client.get(f"{self.result_prefix}{task_id}")
            if result:
                return json.loads(result)
            time.sleep(0.5)
        return {'status': 'timeout'}
    
    def get_queue_length(self):
        return self.redis_client.llen(self.queue_name)

class Worker:
    def __init__(self, task_queue, worker_id=1):
        self.task_queue = task_queue
        self.worker_id = worker_id
        self.running = True
    
    def register_task_handler(self, task_type, handler):
        self.handlers[task_type] = handler
    
    def process_task(self, task):
        print(f"[Worker {self.worker_id}] Processing task {task['id']}: {task['type']}")
        try:
            # Simulate processing time
            time.sleep(task.get('payload', {}).get('duration', 1))
            
            # Task-specific processing
            if task['type'] == 'add':
                result = task['payload']['a'] + task['payload']['b']
            elif task['type'] == 'multiply':
                result = task['payload']['a'] * task['payload']['b']
            elif task['type'] == 'sleep':
                time.sleep(task['payload'].get('seconds', 2))
                result = f"Slept for {task['payload'].get('seconds', 2)} seconds"
            else:
                result = f"Unknown task type: {task['type']}"
            
            self.task_queue.complete_task(task['id'], result)
            print(f"[Worker {self.worker_id}] Completed task {task['id']}: {result}")
        except Exception as e:
            self.task_queue.fail_task(task['id'], e)
            print(f"[Worker {self.worker_id}] Task {task['id']} failed: {e}")
    
    def run(self):
        print(f"[Worker {self.worker_id}] Started, waiting for tasks...")
        while self.running:
            task = self.task_queue.dequeue()
            if task:
                self.process_task(task)
    
    def stop(self):
        self.running = False

def main():
    print("=== Distributed Task Queue ===")
    mode = input("Run as (master/worker): ").strip().lower()
    
    task_queue = TaskQueue()
    
    if mode == 'master':
        print("\nMaster mode - Enqueue tasks")
        while True:
            print("\n1. Add task (add numbers)")
            print("2. Add task (multiply numbers)")
            print("3. Add task (sleep)")
            print("4. Check task status")
            print("5. View queue length")
            print("6. Exit")
            
            choice = input("\nChoose: ").strip()
            
            if choice == '1':
                a = int(input("a: "))
                b = int(input("b: "))
                delay = int(input("Delay seconds (0 for immediate): ") or 0)
                task_id = task_queue.enqueue('add', {'a': a, 'b': b}, delay=delay)
                print(f"Task enqueued: {task_id}")
            
            elif choice == '2':
                a = int(input("a: "))
                b = int(input("b: "))
                task_id = task_queue.enqueue('multiply', {'a': a, 'b': b})
                print(f"Task enqueued: {task_id}")
            
            elif choice == '3':
                seconds = int(input("Sleep seconds: "))
                task_id = task_queue.enqueue('sleep', {'seconds': seconds})
                print(f"Task enqueued: {task_id}")
            
            elif choice == '4':
                task_id = input("Task ID: ").strip()
                result = task_queue.get_result(task_id)
                print(f"Status: {result}")
            
            elif choice == '5':
                print(f"Queue length: {task_queue.get_queue_length()}")
            
            elif choice == '6':
                break
    
    elif mode == 'worker':
        worker_id = int(input("Worker ID: ") or 1)
        worker = Worker(task_queue, worker_id)
        
        def signal_handler(sig, frame):
            print("\nShutting down worker...")
            worker.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        worker.run()

if __name__ == "__main__":
    main()
