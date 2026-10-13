import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.node.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class JsonProcessor {
    private final ObjectMapper mapper = new ObjectMapper()
        .enable(SerializationFeature.INDENT_OUTPUT);

    public JsonNode parseFile(String path) throws IOException {
        return mapper.readTree(Paths.get(path).toFile());
    }

    public JsonNode parseString(String json) throws IOException {
        return mapper.readTree(json);
    }

    public String prettyPrint(JsonNode node) throws IOException {
        return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(node);
    }

    public List<JsonNode> queryPath(JsonNode root, String path) {
        List<JsonNode> results = new ArrayList<>();
        String[] parts = path.split("\\.");
        
        queryPathRecursive(root, parts, 0, results);
        return results;
    }

    private void queryPathRecursive(JsonNode node, String[] parts, int index, List<JsonNode> results) {
        if (index >= parts.length) {
            results.add(node);
            return;
        }
        
        String part = parts[index];
        if (node.isArray()) {
            for (JsonNode child : node) {
                queryPathRecursive(child, parts, index, results);
            }
        } else if (node.isObject()) {
            JsonNode child = node.get(part);
            if (child != null) {
                queryPathRecursive(child, parts, index + 1, results);
            }
        }
    }

    public List<JsonNode> filterArray(ArrayNode array, String field, String operator, String value) {
        return StreamSupport.stream(array.spliterator(), false)
            .filter(node -> {
                JsonNode fieldNode = node.get(field);
                if (fieldNode == null) return false;
                
                switch (operator) {
                    case "==": return fieldNode.asText().equals(value);
                    case ">": return fieldNode.asDouble() > Double.parseDouble(value);
                    case "<": return fieldNode.asDouble() < Double.parseDouble(value);
                    case "contains": return fieldNode.asText().contains(value);
                    default: return false;
                }
            })
            .collect(Collectors.toList());
    }

    public String toCsv(JsonNode node) throws IOException {
        if (!node.isArray()) {
            throw new IllegalArgumentException("Node must be an array for CSV conversion");
        }
        
        Set<String> headers = new LinkedHashSet<>();
        for (JsonNode item : node) {
            item.fields().forEachRemaining(entry -> headers.add(entry.getKey()));
        }
        
        StringBuilder csv = new StringBuilder();
        csv.append(String.join(",", headers)).append("\n");
        
        for (JsonNode item : node) {
            List<String> values = new ArrayList<>();
            for (String header : headers) {
                JsonNode val = item.get(header);
                values.add(val != null ? val.asText() : "");
            }
            csv.append(String.join(",", values)).append("\n");
        }
        
        return csv.toString();
    }

    public static void main(String[] args) throws IOException {
        JsonProcessor processor = new JsonProcessor();
        
        String json = "{\"users\": [" +
            "{\"name\": \"Alice\", \"age\": 25, \"city\": \"NYC\"}," +
            "{\"name\": \"Bob\", \"age\": 30, \"city\": \"LA\"}," +
            "{\"name\": \"Carol\", \"age\": 22, \"city\": \"NYC\"}" +
            "]}";
        
        JsonNode root = processor.parseString(json);
        
        System.out.println("Pretty JSON:");
        System.out.println(processor.prettyPrint(root));
        
        System.out.println("\nQuery: users.name");
        processor.queryPath(root, "users.name").forEach(System.out::println);
        
        System.out.println("\nFilter users where city == NYC:");
        ArrayNode users = (ArrayNode) root.get("users");
        processor.filterArray(users, "city", "==", "NYC")
            .forEach(System.out::println);
        
        System.out.println("\nCSV output:");
        System.out.println(processor.toCsv(users));
    }
}
// Add to pom.xml: com.fasterxml.jackson.core:jackson-databind:2.15.0
