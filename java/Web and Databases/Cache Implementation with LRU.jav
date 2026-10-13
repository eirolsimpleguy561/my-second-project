import java.util.*;
import java.util.concurrent.locks.*;
import java.util.concurrent.atomic.AtomicLong;

class CacheEntry<V> {
    private final V value;
    private final long timestamp;

    public CacheEntry(V value) {
        this.value = value;
        this.timestamp = System.currentTimeMillis();
    }

    public V getValue() { return value; }
    public long getTimestamp() { return timestamp; }
    public boolean isExpired(long ttlMillis) {
        return System.currentTimeMillis() - timestamp > ttlMillis;
    }
}

public class LRUCache<K, V> {
    private final int maxSize;
    private final long ttlMillis;
    private final LinkedHashMap<K, CacheEntry<V>> cache;
    private final ReentrantReadWriteLock lock = new ReentrantReadWriteLock();
    private final AtomicLong hits = new AtomicLong();
    private final AtomicLong misses = new AtomicLong();

    public LRUCache(int maxSize, long ttlMillis) {
        this.maxSize = maxSize;
        this.ttlMillis = ttlMillis;
        this.cache = new LinkedHashMap<K, CacheEntry<V>>(maxSize, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<K, CacheEntry<V>> eldest) {
                return size() > maxSize;
            }
        };
    }

    public V get(K key) {
        lock.readLock().lock();
        try {
            CacheEntry<V> entry = cache.get(key);
            if (entry == null) {
                misses.incrementAndGet();
                return null;
            }
            if (entry.isExpired(ttlMillis)) {
                cache.remove(key);
                misses.incrementAndGet();
                return null;
            }
            hits.incrementAndGet();
            return entry.getValue();
        } finally {
            lock.readLock().unlock();
        }
    }

    public void put(K key, V value) {
        lock.writeLock().lock();
        try {
            cache.put(key, new CacheEntry<>(value));
        } finally {
            lock.writeLock().unlock();
        }
    }

    public void remove(K key) {
        lock.writeLock().lock();
        try {
            cache.remove(key);
        } finally {
            lock.writeLock().unlock();
        }
    }

    public void clear() {
        lock.writeLock().lock();
        try {
            cache.clear();
            hits.set(0);
            misses.set(0);
        } finally {
            lock.writeLock().unlock();
        }
    }

    public void printStats() {
        long total = hits.get() + misses.get();
        double hitRate = total > 0 ? (double) hits.get() / total * 100 : 0;
        System.out.printf("Cache Stats - Hits: %d, Misses: %d, Hit Rate: %.2f%%%n",
            hits.get(), misses.get(), hitRate);
    }

    public int size() {
        lock.readLock().lock();
        try {
            return cache.size();
        } finally {
            lock.readLock().unlock();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        LRUCache<String, String> cache = new LRUCache<>(3, 2000);

        cache.put("A", "Value1");
        cache.put("B", "Value2");
        cache.put("C", "Value3");
        cache.put("D", "Value4"); // A should be evicted

        System.out.println("Get A: " + cache.get("A")); // null (evicted)
        System.out.println("Get B: " + cache.get("B"));
        System.out.println("Get C: " + cache.get("C"));
        System.out.println("Get D: " + cache.get("D"));

        cache.printStats();

        // Test TTL
        System.out.println("\nWaiting 3 seconds for TTL...");
        Thread.sleep(3000);
        System.out.println("Get B: " + cache.get("B")); // null (expired)
        cache.printStats();
    }
}
