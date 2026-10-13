import javax.websocket.*;
import javax.websocket.server.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import com.fasterxml.jackson.databind.*;

class StockPrice {
    private String symbol;
    private double price;
    private long timestamp;

    public StockPrice(String symbol, double price) {
        this.symbol = symbol;
        this.price = price;
        this.timestamp = System.currentTimeMillis();
    }

    // Getters and setters for JSON serialization
    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    public double getPrice() { return price; }
    public void setPrice(double price) { this.price = price; }
    public long getTimestamp() { return timestamp; }
    public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
}

class PriceGenerator {
    private final Map<String, Double> prices = new ConcurrentHashMap<>();
    private final Random random = new Random();

    public PriceGenerator() {
        // Initialize prices
        prices.put("AAPL", 150.0 + random.nextDouble() * 50);
        prices.put("GOOGL", 2800.0 + random.nextDouble() * 100);
        prices.put("MSFT", 350.0 + random.nextDouble() * 30);
        prices.put("AMZN", 3300.0 + random.nextDouble() * 100);
        prices.put("TSLA", 700.0 + random.nextDouble() * 100);
    }

    public StockPrice generatePrice(String symbol) {
        double current = prices.get(symbol);
        double change = (random.nextDouble() - 0.5) * 5;
        double newPrice = Math.max(1, current + change);
        prices.put(symbol, newPrice);
        return new StockPrice(symbol, newPrice);
    }

    public Set<String> getSymbols() {
        return prices.keySet();
    }
}

@ServerEndpoint("/stocks")
public class StockWebSocket {
    private static final Set<Session> sessions = ConcurrentHashMap.newKeySet();
    private static final Map<Session, Set<String>> subscriptions = new ConcurrentHashMap<>();
    private static final PriceGenerator priceGenerator = new PriceGenerator();
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    private static final AtomicBoolean running = new AtomicBoolean(false);

    @OnOpen
    public void onOpen(Session session) {
        sessions.add(session);
        subscriptions.put(session, ConcurrentHashMap.newKeySet());
        System.out.println("WebSocket connected: " + session.getId());
        
        // Start price updates if not running
        if (!running.get()) {
            startPriceUpdates();
        }
    }

    @OnMessage
    public void onMessage(String message, Session session) throws IOException {
        System.out.println("Received: " + message);
        
        try {
            JsonNode json = mapper.readTree(message);
            String action = json.get("action").asText();
            
            if ("subscribe".equals(action)) {
                String symbol = json.get("symbol").asText().toUpperCase();
                if (priceGenerator.getSymbols().contains(symbol)) {
                    subscriptions.get(session).add(symbol);
                    session.getBasicRemote().sendText("Subscribed to: " + symbol);
                }
            } else if ("unsubscribe".equals(action)) {
                String symbol = json.get("symbol").asText().toUpperCase();
                subscriptions.get(session).remove(symbol);
                session.getBasicRemote().sendText("Unsubscribed from: " + symbol);
            } else if ("list".equals(action)) {
                session.getBasicRemote().sendText("Available: " + priceGenerator.getSymbols());
            }
        } catch (Exception e) {
            session.getBasicRemote().sendText("Error: " + e.getMessage());
        }
    }

    @OnClose
    public void onClose(Session session) {
        sessions.remove(session);
        subscriptions.remove(session);
        System.out.println("WebSocket disconnected: " + session.getId());
        
        if (sessions.isEmpty()) {
            running.set(false);
        }
    }

    @OnError
    public void onError(Session session, Throwable error) {
        System.err.println("WebSocket error: " + error.getMessage());
        sessions.remove(session);
        subscriptions.remove(session);
    }

    private static void startPriceUpdates() {
        running.set(true);
        scheduler.scheduleAtFixedRate(() -> {
            if (sessions.isEmpty() || !running.get()) {
                return;
            }
            
            // Generate new prices
            Map<String, Double> updates = new HashMap<>();
            for (String symbol : priceGenerator.getSymbols()) {
                StockPrice price = priceGenerator.generatePrice(symbol);
                updates.put(symbol, price.getPrice());
            }

            // Send updates to subscribed clients
            for (Session session : sessions) {
                Set<String> subscribed = subscriptions.get(session);
                if (subscribed == null || subscribed.isEmpty()) continue;

                Map<String, Double> relevantUpdates = new HashMap<>();
                for (String symbol : subscribed) {
                    if (updates.containsKey(symbol)) {
                        relevantUpdates.put(symbol, updates.get(symbol));
                    }
                }

                if (!relevantUpdates.isEmpty()) {
                    try {
                        String json = mapper.writeValueAsString(relevantUpdates);
                        session.getBasicRemote().sendText(json);
                    } catch (IOException e) {
                        System.err.println("Failed to send update: " + e.getMessage());
                    }
                }
            }
        }, 0, 2, TimeUnit.SECONDS);
    }

    public static void stopPriceUpdates() {
        running.set(false);
        scheduler.shutdown();
        try {
            scheduler.awaitTermination(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) {
        System.out.println("WebSocket server running at: ws://localhost:8080/stocks");
        
        // Keep server running
        try {
            Thread.sleep(Long.MAX_VALUE);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}

// Client JavaScript:
/*
const socket = new WebSocket('ws://localhost:8080/stocks');

socket.onopen = () => {
    console.log('Connected');
    // Subscribe to stocks
    socket.send(JSON.stringify({action: 'subscribe', symbol: 'AAPL'}));
    socket.send(JSON.stringify({action: 'subscribe', symbol: 'GOOGL'}));
    // Get available stocks
    socket.send(JSON.stringify({action: 'list'}));
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (typeof data === 'object') {
        // Stock price update
        for (const [symbol, price] of Object.entries(data)) {
            console.log(`${symbol}: $${price.toFixed(2)}`);
        }
    } else {
        console.log('Message:', data);
    }
};

socket.onclose = () => console.log('Disconnected');
*/
