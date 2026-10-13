import com.fasterxml.jackson.databind.*;
import java.net.http.*;
import java.net.URI;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;

class StockData {
    private String symbol;
    private double price;
    private double previousClose;
    private double changePercent;
    private String timestamp;

    public void parseFromAlphaVantage(JsonNode node, String symbol) {
        this.symbol = symbol;
        JsonNode globalQuote = node.get("Global Quote");
        if (globalQuote != null) {
            this.price = Double.parseDouble(globalQuote.get("05. price").asText());
            this.changePercent = Double.parseDouble(
                globalQuote.get("10. change percent").asText().replace("%", "")
            );
            this.timestamp = globalQuote.get("07. latest trading day").asText();
        }
    }

    public String getSymbol() { return symbol; }
    public double getPrice() { return price; }
    public double getChangePercent() { return changePercent; }
    
    @Override
    public String toString() {
        return String.format("%s: $%.2f (%.2f%%)", 
            symbol, price, changePercent);
    }
}

class StockTracker {
    private final HttpClient client = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();
    private final Map<String, Double> priceAlerts = new ConcurrentHashMap<>();
    private final Map<String, StockData> stocks = new ConcurrentHashMap<>();
    private final String apiKey;

    public StockTracker(String apiKey) {
        this.apiKey = apiKey;
    }

    public StockData fetchStock(String symbol) throws Exception {
        String url = String.format(
            "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=%s&apikey=%s",
            symbol, apiKey
        );

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .timeout(Duration.ofSeconds(10))
            .GET()
            .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode root = mapper.readTree(response.body());

        StockData stock = new StockData();
        stock.parseFromAlphaVantage(root, symbol);
        
        // Check alerts
        checkAlerts(stock);
        
        stocks.put(symbol, stock);
        return stock;
    }

    public void setPriceAlert(String symbol, double threshold) {
        priceAlerts.put(symbol, threshold);
        System.out.println("Alert set for " + symbol + " at $" + threshold);
    }

    private void checkAlerts(StockData stock) {
        Double threshold = priceAlerts.get(stock.getSymbol());
        if (threshold != null && stock.getPrice() >= threshold) {
            System.out.println("ALERT: " + stock.getSymbol() + " reached $" + stock.getPrice() + 
                " (Threshold: $" + threshold + ")");
            // In a real app, send email here
        }
    }

    public void trackMultiple(List<String> symbols) throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(5);
        List<Future<StockData>> futures = new ArrayList<>();

        for (String symbol : symbols) {
            futures.add(executor.submit(() -> fetchStock(symbol)));
        }

        System.out.println("Stock Prices:");
        System.out.println("-".repeat(40));
        for (Future<StockData> future : futures) {
            try {
                System.out.println(future.get(15, TimeUnit.SECONDS));
            } catch (TimeoutException e) {
                System.out.println("Timed out fetching stock");
            }
        }
        executor.shutdown();
    }

    public void startMonitoring(String symbol, int intervalSeconds) {
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        scheduler.scheduleAtFixedRate(() -> {
            try {
                StockData stock = fetchStock(symbol);
                System.out.println(LocalDateTime.now() + " - " + stock);
            } catch (Exception e) {
                System.err.println("Error fetching " + symbol + ": " + e.getMessage());
            }
        }, 0, intervalSeconds, TimeUnit.SECONDS);
    }
}

public class Main {
    public static void main(String[] args) throws Exception {
        String apiKey = System.getenv("ALPHA_VANTAGE_KEY");
        if (apiKey == null) {
            System.out.println("Please set ALPHA_VANTAGE_KEY environment variable");
            return;
        }

        StockTracker tracker = new StockTracker(apiKey);
        
        // Track multiple stocks
        List<String> symbols = Arrays.asList("AAPL", "GOOGL", "MSFT", "AMZN");
        tracker.trackMultiple(symbols);

        // Set alert
        tracker.setPriceAlert("AAPL", 200.0);

        // Monitor a single stock
        tracker.startMonitoring("AAPL", 30);

        // Keep running for 2 minutes
        Thread.sleep(120000);
    }
}
