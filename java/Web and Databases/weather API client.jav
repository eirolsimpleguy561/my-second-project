import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.time.Duration;
import java.util.*;

public class WeatherClient {
    private static final String API_KEY = "YOUR_API_KEY";
    private static final String BASE_URL = "https://api.openweathermap.org/data/2.5/weather";
    private final HttpClient client = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();
    private final Map<String, CacheEntry> cache = new HashMap<>();

    private static class CacheEntry {
        String data;
        long timestamp;
        CacheEntry(String data) {
            this.data = data;
            this.timestamp = System.currentTimeMillis();
        }
        boolean isValid() {
            return System.currentTimeMillis() - timestamp < 300_000; // 5 minutes
        }
    }

    public String getWeather(String city) throws Exception {
        String cached = getCached(city);
        if (cached != null) return cached;

        String url = BASE_URL + "?q=" + city + "&appid=" + API_KEY + "&units=metric";
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .timeout(Duration.ofSeconds(10))
            .GET()
            .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new RuntimeException("Weather API error: " + response.statusCode());
        }

        cache.put(city.toLowerCase(), new CacheEntry(response.body()));
        return parseWeatherData(response.body());
    }

    private String parseWeatherData(String json) throws Exception {
        JsonNode root = mapper.readTree(json);
        String city = root.path("name").asText();
        double temp = root.path("main").path("temp").asDouble();
        double humidity = root.path("main").path("humidity").asDouble();
        String description = root.path("weather").get(0).path("description").asText();

        return String.format("Weather in %s: %.1f°C, %s%%, %s", 
            city, temp, humidity, description);
    }

    private String getCached(String city) {
        CacheEntry entry = cache.get(city.toLowerCase());
        if (entry != null && entry.isValid()) {
            try {
                return parseWeatherData(entry.data);
            } catch (Exception e) {
                return null;
            }
        }
        return null;
    }

    public static void main(String[] args) throws Exception {
        WeatherClient client = new WeatherClient();
        Scanner sc = new Scanner(System.in);
        
        while (true) {
            System.out.print("Enter city (or 'quit'): ");
            String city = sc.nextLine();
            if (city.equalsIgnoreCase("quit")) break;
            
            try {
                System.out.println(client.getWeather(city));
            } catch (Exception e) {
                System.out.println("Error: " + e.getMessage());
            }
        }
        sc.close();
    }
}
// Add to pom.xml: com.fasterxml.jackson.core:jackson-databind
