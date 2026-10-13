import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Document {
    private final String id;
    private final String title;
    private final String content;
    private final Map<String, Integer> termFrequency = new HashMap<>();

    public Document(String id, String title, String content) {
        this.id = id;
        this.title = title;
        this.content = content;
        indexContent();
    }

    private void indexContent() {
        String[] words = content.toLowerCase().split("\\W+");
        for (String word : words) {
            if (word.length() > 1) {
                termFrequency.merge(word, 1, Integer::sum);
            }
        }
    }

    public String getId() { return id; }
    public String getTitle() { return title; }
    public String getContent() { return content; }
    public Map<String, Integer> getTermFrequency() { return termFrequency; }
    
    @Override
    public String toString() {
        return title + " (" + id + ")";
    }
}

class SearchEngine {
    private final Map<String, Map<String, Integer>> invertedIndex = new ConcurrentHashMap<>();
    private final Map<String, Document> documents = new ConcurrentHashMap<>();
    private final Set<String> stopWords = Set.of("the", "a", "an", "of", "to", "for", "with", "on", "at", "in", "is");

    public void addDocument(Document doc) {
        documents.put(doc.getId(), doc);
        
        for (Map.Entry<String, Integer> entry : doc.getTermFrequency().entrySet()) {
            String term = entry.getKey();
            if (stopWords.contains(term)) continue;
            
            Map<String, Integer> docMap = invertedIndex.computeIfAbsent(term, k -> new HashMap<>());
            docMap.put(doc.getId(), entry.getValue());
        }
    }

    public List<Document> search(String query) {
        String[] terms = query.toLowerCase().split(" ");
        Set<String> docIds = new HashSet<>();
        boolean first = true;

        for (String term : terms) {
            if (stopWords.contains(term)) continue;
            
            Map<String, Integer> docs = invertedIndex.get(term);
            if (docs == null) continue;

            if (first) {
                docIds.addAll(docs.keySet());
                first = false;
            } else {
                docIds.retainAll(docs.keySet());
            }
        }

        // Rank results by TF-IDF
        List<Document> results = docIds.stream()
            .map(documents::get)
            .filter(Objects::nonNull)
            .sorted((d1, d2) -> Double.compare(
                calculateScore(query, d2),
                calculateScore(query, d1)
            ))
            .limit(10)
            .collect(Collectors.toList());

        return results;
    }

    private double calculateScore(String query, Document doc) {
        String[] terms = query.toLowerCase().split(" ");
        double score = 0;
        Map<String, Integer> tf = doc.getTermFrequency();
        
        for (String term : terms) {
            if (stopWords.contains(term)) continue;
            Integer freq = tf.get(term);
            if (freq != null) {
                // Simple TF-IDF approximation
                double idf = Math.log(1 + (double) documents.size() / 
                    (1 + invertedIndex.getOrDefault(term, Map.of()).size()));
                score += freq * idf;
            }
        }
        return score;
    }

    public Map<String, Long> getTermFrequency() {
        return invertedIndex.entrySet().stream()
            .collect(Collectors.toMap(
                Map.Entry::getKey,
                e -> (long) e.getValue().size()
            ));
    }

    public static void main(String[] args) {
        SearchEngine engine = new SearchEngine();

        // Add sample documents
        engine.addDocument(new Document("1", "Java Programming", 
            "Java is a popular programming language. Many developers use Java for enterprise applications."));
        engine.addDocument(new Document("2", "Python Tutorial", 
            "Python is great for data science and machine learning. Python has simple syntax."));
        engine.addDocument(new Document("3", "Java vs Python", 
            "Java and Python are both popular languages. Java is statically typed while Python is dynamic."));
        engine.addDocument(new Document("4", "JavaScript Guide", 
            "JavaScript is used for web development. It runs in the browser."));

        // Search
        List<Document> results = engine.search("Java language");
        System.out.println("Search results for 'Java language':");
        results.forEach(doc -> {
            System.out.println("  - " + doc);
            String snippet = doc.getContent().substring(0, Math.min(60, doc.getContent().length()));
            System.out.println("    " + snippet + "...");
        });

        System.out.println("\nInverted Index Statistics:");
        engine.getTermFrequency().entrySet().stream()
            .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
            .limit(10)
            .forEach(entry -> System.out.println("  " + entry.getKey() + ": " + entry.getValue() + " docs"));
    }
}
