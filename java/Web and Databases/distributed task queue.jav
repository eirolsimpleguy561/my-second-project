// === pom.xml dependencies ===
// jedis, slf4j-simple

import redis.clients.jedis.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Consumer;
import java.time.*;

class TaskQueue {
    private final JedisPool jedisPool;
    private final String queueKey;
    private final String processingKey;
    private final String delayedKey;

    public TaskQueue(String host, int port) {
        this.jedisPool = new JedisPool(host, port);
        this.queueKey = "tasks:queue";
        this.processingKey = "tasks:processing";
        this.delayedKey = "tasks:delayed";
    }

    public void enqueue(String task, int priority, long delayMs) {
        try (Jedis jedis = jedisPool.getResource()) {
            String taskData = String.format("%s|%d", task, System.currentTimeMillis());
            
            if (delayMs > 0) {
                long readyTime = System.currentTimeMillis() + delayMs;
                jedis.zadd(delayedKey, readyTime, taskData);
                System.out.println("Task delayed until " + new Date(readyTime));
            } else {
                jedis.zadd(queueKey, priority, taskData);
                System.out.println("Task enqueued with priority " + priority);
            }
        }
    }

    public String dequeue() {
        try (Jedis jedis = jedisPool.getResource()) {
            // Move delayed tasks to queue
            moveDelayedTasks(jedis);

            String taskData = jedis.zpopmin(queueKey);
            if (taskData != null) {
                jedis.sadd(processingKey, taskData);
                return taskData;
            }
            return null;
        }
    }

    private void moveDelayedTasks(Jedis jedis) {
        long now = System.currentTimeMillis();
        Set<String> delayedTasks = jedis.zrangeByScore(delayedKey, 0, now);
        for (String task : delayedTasks) {
            jedis.zadd(queueKey, 5, task); // Medium priority for delayed tasks
            jedis.zrem(delayedKey, task);
        }
    }

    public void acknowledge(String taskData) {
        try (Jedis jedis = jedisPool.getResource()) {
            jedis.srem(processingKey, taskData);
        }
    }

    public List<String> getProcessingTasks() {
        try (Jedis jedis = jedisPool.getResource()) {
            return new ArrayList<>(jedis.smembers(processingKey));
        }
    }

    public void close() {
        jedisPool.close();
    }
}

class Worker {
    private final TaskQueue queue;
    private final String name;
    private final Consumer<String> taskHandler;
    private volatile boolean running = true;

    public Worker(TaskQueue queue, String name, Consumer<String> taskHandler) {
        this.queue = queue;
        this.name = name;
        this.taskHandler = taskHandler;
    }

    public void start() {
        Thread thread = new Thread(() -> {
            while (running) {
                try {
                    String task = queue.dequeue();
                    if (task != null) {
                        System.out.println(name + " processing: " + task);
                        taskHandler.accept(task);
                        queue.acknowledge(task);
                        System.out.println(name + " completed: " + task);
                    } else {
                        Thread.sleep(1000);
                    }
                } catch (Exception e) {
                    System.err.println(name + " error: " + e.getMessage());
                }
            }
        });
        thread.start();
    }

    public void stop() {
        running = false;
    }
}

public class Main {
    public static void main(String[] args) throws InterruptedException {
        TaskQueue queue = new TaskQueue("localhost", 6379);

        // Create workers
        Consumer<String> handler = (task) -> {
            try {
                String[] parts = task.split("\\|");
                String taskData = parts[0];
                int sleepTime = (int) (Math.random() * 3000);
                Thread.sleep(sleepTime);
                System.out.println("Executed: " + taskData + " (took " + sleepTime + "ms)");
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };

        Worker worker1 = new Worker(queue, "Worker-1", handler);
        Worker worker2 = new Worker(queue, "Worker-2", handler);
        
        worker1.start();
        worker2.start();

        // Enqueue tasks with different priorities
        queue.enqueue("Task-A", 1, 0);  // High priority
        queue.enqueue("Task-B", 5, 0);  // Medium priority
        queue.enqueue("Task-C", 10, 0); // Low priority
        queue.enqueue("Task-D", 3, 2000); // Delayed 2 seconds
        queue.enqueue("Task-E", 2, 0);  // High priority

        // Monitor processing
        Thread.sleep(1000);
        System.out.println("\nProcessing tasks: " + queue.getProcessingTasks());

        Thread.sleep(10000); // Let workers process

        worker1.stop();
        worker2.stop();
        queue.close();
    }
}
