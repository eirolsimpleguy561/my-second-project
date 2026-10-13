import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Consumer;
import java.time.*;

class FileEvent {
    private final Path path;
    private final WatchEvent.Kind<Path> kind;
    private final LocalDateTime timestamp;

    public FileEvent(Path path, WatchEvent.Kind<Path> kind) {
        this.path = path;
        this.kind = kind;
        this.timestamp = LocalDateTime.now();
    }

    public Path getPath() { return path; }
    public WatchEvent.Kind<Path> getKind() { return kind; }
    public LocalDateTime getTimestamp() { return timestamp; }

    @Override
    public String toString() {
        return String.format("[%s] %s: %s", timestamp, kind.name(), path);
    }
}

class FileMonitor {
    private final WatchService watchService;
    private final Map<Path, WatchKey> watchedDirectories = new HashMap<>();
    private final List<Consumer<FileEvent>> listeners = new ArrayList<>();
    private final Set<String> extensions = new HashSet<>();
    private boolean running = true;

    public FileMonitor() throws Exception {
        this.watchService = FileSystems.getDefault().newWatchService();
        
        // Default extensions
        extensions.addAll(Arrays.asList(".txt", ".java", ".pdf", ".xml", ".json"));
    }

    public void addListener(Consumer<FileEvent> listener) {
        listeners.add(listener);
    }

    public void addExtension(String extension) {
        extensions.add(extension);
    }

    public void addDirectory(Path path) throws Exception {
        if (!Files.exists(path)) {
            Files.createDirectories(path);
        }
        
        WatchKey key = path.register(watchService,
            StandardWatchEventKinds.ENTRY_CREATE,
            StandardWatchEventKinds.ENTRY_MODIFY,
            StandardWatchEventKinds.ENTRY_DELETE
        );
        
        watchedDirectories.put(path, key);
        System.out.println("Watching: " + path);
    }

    private boolean isRelevantFile(Path path) {
        String fileName = path.toString().toLowerCase();
        return extensions.stream().anyMatch(fileName::endsWith);
    }

    public void startMonitoring() {
        Thread monitorThread = new Thread(() -> {
            while (running) {
                try {
                    WatchKey key = watchService.poll(5, TimeUnit.SECONDS);
                    if (key == null) continue;

                    for (WatchEvent<?> event : key.pollEvents()) {
                        WatchEvent.Kind<?> kind = event.kind();

                        if (kind == StandardWatchEventKinds.OVERFLOW) continue;

                        Path dir = (Path) key.watchable();
                        Path child = dir.resolve((Path) event.context());

                        if (isRelevantFile(child)) {
                            FileEvent fileEvent = new FileEvent(child, (WatchEvent.Kind<Path>) kind);
                            notifyListeners(fileEvent);
                        }
                    }

                    boolean valid = key.reset();
                    if (!valid) {
                        watchedDirectories.entrySet().removeIf(entry -> entry.getValue() == key);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        });
        
        monitorThread.start();
        System.out.println("File monitor started");
    }

    private void notifyListeners(FileEvent event) {
        for (Consumer<FileEvent> listener : listeners) {
            try {
                listener.accept(event);
            } catch (Exception e) {
                System.err.println("Listener error: " + e.getMessage());
            }
        }
    }

    public void stop() {
        running = false;
        try {
            watchService.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) throws Exception {
        FileMonitor monitor = new FileMonitor();

        // Add listeners
        monitor.addListener(event -> {
            System.out.println("File event: " + event);
            if (event.getKind() == StandardWatchEventKinds.ENTRY_CREATE) {
                System.out.println("Processing new file: " + event.getPath().getFileName());
                // In real app, process the file here
            }
        });

        monitor.addListener(event -> {
            // Log to a file
            System.out.println("LOG: " + event);
        });

        // Add directories
        Path watchDir = Paths.get("./monitor");
        monitor.addDirectory(watchDir);

        // Start monitoring
        monitor.startMonitoring();

        System.out.println("Place files in ./monitor to test");
        System.out.println("Press Enter to stop...");
        new Scanner(System.in).nextLine();

        monitor.stop();
        System.out.println("Monitor stopped");
    }
}
