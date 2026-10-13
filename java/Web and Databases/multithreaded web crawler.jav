import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.*;

public class WebCrawler {
    private final Set<String> visited = ConcurrentHashMap.newKeySet();
    private final ExecutorService pool = Executors.newFixedThreadPool(8);
    private final int maxDepth;
    private final int maxPages;
    private final List<String> results = Collections.synchronizedList(new ArrayList<>());

    public WebCrawler(int maxDepth, int maxPages) {
        this.maxDepth = maxDepth;
        this.maxPages = maxPages;
    }

    public void crawl(String startUrl) throws InterruptedException {
        List<Future<?>> futures = new ArrayList<>();
        futures.add(pool.submit(() -> crawlPage(startUrl, 0)));

        // Wait for all tasks to complete
        for (Future<?> f : futures) {
            try { f.get(30, TimeUnit.SECONDS); } catch (Exception e) { /* timeout */ }
        }

        pool.shutdown();
        pool.awaitTermination(60, TimeUnit.SECONDS);

        System.out.println("\n=== Crawl Results ===");
        results.forEach(System.out::println);
        System.out.println("\nTotal pages crawled: " + results.size());
    }

    private void crawlPage(String url, int depth) {
        if (depth > maxDepth || visited.size() >= maxPages) return;
        if (!visited.add(url)) return;

        try {
            Document doc = Jsoup.connect(url)
                .userAgent("Mozilla/5.0")
                .timeout(5000)
                .get();

            String title = doc.title();
            results.add(String.format("[Depth %d] %s | %s", depth, title, url));
            System.out.println("Crawled: " + url);

            if (depth < maxDepth) {
                Elements links = doc.select("a[href]");
                List<Future<?>> futures = new ArrayList<>();
                for (var link : links) {
                    String nextUrl = link.absUrl("href");
                    if (!nextUrl.isEmpty() && nextUrl.startsWith("http") && !visited.contains(nextUrl)) {
                        futures.add(pool.submit(() -> crawlPage(nextUrl, depth + 1)));
                    }
                }
                for (Future<?> f : futures) {
                    try { f.get(10, TimeUnit.SECONDS); } catch (Exception e) { /* skip */ }
                }
            }
        } catch (IOException e) {
            System.out.println("Failed: " + url + " — " + e.getMessage());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        WebCrawler crawler = new WebCrawler(2, 20);
        crawler.crawl("https://example.com");
    }
}
// Add to pom.xml: org.jsoup:jsoup:1.17.2
