import java.net.http.*;
import java.net.URI;
import java.time.Duration;
import java.util.concurrent.*;
import java.util.function.Predicate;
import java.util.*;

public class ResilientHttpClient {
    private final HttpClient client;
    private final int maxRetries;
    private final Duration initialBackoff;
    private final Predicate<HttpResponse<String>> shouldRetry;
    private final CircuitBreaker circuitBreaker;
    private final RequestLogger logger = new RequestLogger();

    public ResilientHttpClient(int maxRetries, Duration initialBackoff, int failureThreshold) {
        this.maxRetries = maxRetries;
        this.initialBackoff = initialBackoff;
        this.circuitBreaker = new CircuitBreaker(failureThreshold);
        this.shouldRetry = response -> response.statusCode() >= 500 || 
                                      response.statusCode() == 429;
        this.client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    }

    public HttpResponse<String> get(String url) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .timeout(Duration.ofSeconds(30))
            .header("User-Agent", "ResilientClient/1.0")
            .GET()
            .build();

        return executeWithRetry(request);
    }

    private HttpResponse<String> executeWithRetry(HttpRequest request) throws Exception {
        logger.logRequest(request);

        if (!circuitBreaker.isOpen()) {
            throw new RuntimeException("Circuit breaker is OPEN");
        }

        int attempts = 0;
        while (attempts <= maxRetries) {
            try {
                HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
                logger.logResponse(response);

                if (!shouldRetry.test(response)) {
                    circuitBreaker.recordSuccess();
                    return response;
                }

                // Rate limiting
                if (response.statusCode() == 429) {
                    long waitTime = getRetryAfter(response);
                    Thread.sleep(waitTime);
                }

            } catch (Exception e) {
                logger.logError(e);
                circuitBreaker.recordFailure();
                
                if (attempts == maxRetries) {
                    throw new RuntimeException("Max retries exceeded", e);
                }
            }

            attempts++;
            if (attempts <= maxRetries) {
                long backoffTime = (long) (initialBackoff.toMillis() * Math.pow(2, attempts - 1));
                System.out.println("Retry " + attempts + " in " + backoffTime + "ms");
                Thread.sleep(backoffTime);
            }
        }

        throw new RuntimeException("Failed after " + maxRetries + " retries");
    }

    private long getRetryAfter(HttpResponse<String> response) {
        String retryAfter = response.headers().firstValue("Retry-After").orElse("5");
        try {
            return Long.parseLong(retryAfter) * 1000;
        } catch (NumberFormatException e) {
            return 5000; // Default 5 seconds
        }
    }

    // Circuit Breaker implementation
    static class CircuitBreaker {
        private final int failureThreshold;
        private int consecutiveFailures = 0;
        private boolean isOpen = false;
        private long lastFailureTime = 0;
        private static final long RESET_TIMEOUT = 60000; // 60 seconds

        public CircuitBreaker(int failureThreshold) {
            this.failureThreshold = failureThreshold;
        }

        public synchronized boolean isOpen() {
            if (isOpen) {
                if (System.currentTimeMillis() - lastFailureTime > RESET_TIMEOUT) {
                    isOpen = false;
                    consecutiveFailures = 0;
                    System.out.println("Circuit breaker reset");
                    return true;
                }
                return false;
            }
            return true;
        }

        public synchronized void recordSuccess() {
            if (!isOpen) {
                consecutiveFailures = 0;
            }
        }

        public synchronized void recordFailure() {
            consecutiveFailures++;
            if (consecutiveFailures >= failureThreshold) {
                isOpen = true;
                lastFailureTime = System.currentTimeMillis();
                System.out.println("Circuit breaker OPENED");
            }
        }
    }

    static class RequestLogger {
        public void logRequest(HttpRequest request) {
            System.out.println("REQUEST: " + request.method() + " " + request.uri());
        }

        public void logResponse(HttpResponse<String> response) {
            System.out.println("RESPONSE: " + response.statusCode() + " " + response.uri());
        }

        public void logError(Exception e) {
            System.out.println("ERROR: " + e.getMessage());
        }
    }

    public static void main(String[] args) throws Exception {
        ResilientHttpClient client = new ResilientHttpClient(3, Duration.ofSeconds(1), 3);
        
        // Test with a working API
        try {
            HttpResponse<String> response = client.get("https://jsonplaceholder.typicode.com/posts/1");
            System.out.println("Response body: " + response.body().substring(0, 100));
        } catch (Exception e) {
            System.err.println("Failed: " + e.getMessage());
        }

        // Test with a failing endpoint
        try {
            HttpResponse<String> response = client.get("https://httpstat.us/500");
        } catch (Exception e) {
            System.err.println("Failed after retries: " + e.getMessage());
        }
    }
}
