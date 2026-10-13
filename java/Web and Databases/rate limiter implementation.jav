import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.time.*;

class TokenBucket {
    private final long capacity;
    private final double refillRate; // tokens per second
    private final AtomicLong tokens;
    private volatile long lastRefillTime;
    private final Object lock = new Object();

    public TokenBucket(long capacity, double refillRate) {
        this.capacity = capacity;
        this.refillRate = refillRate;
        this.tokens = new AtomicLong(capacity);
        this.lastRefillTime = System.nanoTime();
    }

    private void refill() {
        long now = System.nanoTime();
        long elapsed = now - lastRefillTime;
        double tokensToAdd = elapsed / 1_000_000_000.0 * refillRate;
        
        if (tokensToAdd > 0) {
            long newTokens = Math.min(capacity, tokens.get() + (long) tokensToAdd);
            tokens.set(newTokens);
            lastRefillTime = now;
        }
    }

    public boolean allowRequest() {
        synchronized (lock) {
            refill();
            if (tokens.get() > 0) {
                tokens.decrementAndGet();
                return true;
            }
            return false;
        }
    }

    public long getAvailableTokens() {
        synchronized (lock) {
            refill();
            return tokens.get();
        }
    }
}

class RateLimiter {
    private final TokenBucket tokenBucket;
    private final AtomicLong totalRequests = new AtomicLong();
    private final AtomicLong allowedRequests = new AtomicLong();
    private final AtomicLong rejectedRequests = new AtomicLong();

    public RateLimiter(long capacity, double refillRate) {
        this.tokenBucket = new TokenBucket(capacity, refillRate);
    }

    public boolean isAllowed() {
        totalRequests.incrementAndGet();
        boolean allowed = tokenBucket.allowRequest();
        
        if (allowed) {
            allowedRequests.incrementAndGet();
        } else {
            rejectedRequests.incrementAndGet();
        }
        
        return allowed;
    }

    public void printStats() {
        long total = totalRequests.get();
        long allowed = allowedRequests.get();
        long rejected = rejectedRequests.get();
        double acceptRate = total > 0 ? (double) allowed / total * 100 : 0;
        
        System.out.println("=== Rate Limiter Stats ===");
        System.out.println("Total Requests: " + total);
        System.out.println("Allowed: " + allowed + " (" + String.format("%.2f", acceptRate) + "%)");
        System.out.println("Rejected: " + rejected);
        System.out.println("Available Tokens: " + tokenBucket.getAvailableTokens());
    }
}

class ApiClient {
    private final RateLimiter rateLimiter;
    private final String name;

    public ApiClient(String name, RateLimiter rateLimiter) {
        this.name = name;
        this.rateLimiter = rateLimiter;
    }

    public void callApi() {
        if (rateLimiter.isAllowed()) {
            System.out.println(name + ": Request allowed");
            try {
                Thread.sleep(10); // Simulate API call
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        } else {
            System.out.println(name + ": Request REJECTED");
        }
    }
}

public class Main {
    public static void main(String[] args) throws InterruptedException {
        // Limit to 10 requests per second, burst capacity of 20
        RateLimiter rateLimiter = new RateLimiter(20, 10);

        // Create multiple clients
        List<ApiClient> clients = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            clients.add(new ApiClient("Client-" + i, rateLimiter));
        }

        // Simulate traffic
        ExecutorService executor = Executors.newFixedThreadPool(5);
        for (int round = 0; round < 30; round++) {
            for (ApiClient client : clients) {
                executor.submit(client::callApi);
            }
            Thread.sleep(100); // 100ms between rounds
        }

        executor.shutdown();
        executor.awaitTermination(10, TimeUnit.SECONDS);

        rateLimiter.printStats();

        // Test burst behavior
        System.out.println("\n=== Testing Burst ===");
        RateLimiter burstLimiter = new RateLimiter(10, 2);
        
        // First 10 requests should all succeed (burst)
        for (int i = 0; i < 12; i++) {
            boolean allowed = burstLimiter.isAllowed();
            System.out.println("Request " + (i + 1) + ": " + (allowed ? "OK" : "REJECTED"));
        }
    }
}

// === Redis-based Distributed Rate Limiter ===
/*
import redis.clients.jedis.*;

class RedisRateLimiter {
    private final JedisPool jedisPool;
    private final String key;
    private final long capacity;
    private final long refillIntervalMs;
    private final long refillAmount;

    public RedisRateLimiter(String key, long capacity, long refillIntervalMs, long refillAmount) {
        this.jedisPool = new JedisPool("localhost", 6379);
        this.key = key;
        this.capacity = capacity;
        this.refillIntervalMs = refillIntervalMs;
        this.refillAmount = refillAmount;
    }

    public boolean allowRequest() {
        try (Jedis jedis = jedisPool.getResource()) {
            String luaScript = 
                "local key = KEYS[1]\n" +
                "local capacity = tonumber(ARGV[1])\n" +
                "local refillAmount = tonumber(ARGV[2])\n" +
                "local refillInterval = tonumber(ARGV[3])\n" +
                "\n" +
                "local current = redis.call('hget', key, 'tokens')\n" +
                "if current == false then\n" +
                "  redis.call('hset', key, 'tokens', capacity)\n" +
                "  redis.call('hset', key, 'last_refill', redis.call('time')[1])\n" +
                "  current = capacity\n" +
                "end\n" +
                "\n" +
                "local last_refill = redis.call('hget', key, 'last_refill')\n" +
                "local now = redis.call('time')[1]\n" +
                "local elapsed = now - last_refill\n" +
                "local tokensToAdd = math.floor(elapsed / refillInterval) * refillAmount\n" +
                "\n" +
                "if tokensToAdd > 0 then\n" +
                "  current = math.min(capacity, current + tokensToAdd)\n" +
                "  redis.call('hset', key, 'last_refill', now)\n" +
                "end\n" +
                "\n" +
                "if current > 0 then\n" +
                "  redis.call('hset', key, 'tokens', current - 1)\n" +
                "  return 1\n" +
                "end\n" +
                "return 0";
                
            String sha = jedis.scriptLoad(luaScript);
            Long result = (Long) jedis.evalsha(sha, 1, key, 
                String.valueOf(capacity), 
                String.valueOf(refillAmount), 
                String.valueOf(refillIntervalMs / 1000));
            return result == 1;
        }
    }
}
*/
