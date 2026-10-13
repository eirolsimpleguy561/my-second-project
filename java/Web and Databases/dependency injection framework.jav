import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

// === Annotations ===
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@interface Component {}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.CONSTRUCTOR)
@interface Inject {}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface PostConstruct {}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface PreDestroy {}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@interface Scope {
    String value() default "singleton";
}

// === Component Definitions ===
@Component
@Scope("singleton")
class Logger {
    public void log(String message) {
        System.out.println("[LOG] " + message);
    }
}

@Component
class DatabaseConnection {
    private String url = "jdbc:mysql://localhost:3306/db";

    @PostConstruct
    public void connect() {
        System.out.println("Connected to database: " + url);
    }

    @PreDestroy
    public void disconnect() {
        System.out.println("Disconnected from database");
    }

    public void executeQuery(String query) {
        System.out.println("Executing: " + query);
    }
}

@Component
class UserService {
    @Inject
    private DatabaseConnection db;
    
    @Inject
    private Logger logger;

    public void createUser(String name) {
        logger.log("Creating user: " + name);
        db.executeQuery("INSERT INTO users (name) VALUES ('" + name + "')");
    }
}

// === Dependency Injection Container ===
class Container {
    private final Map<Class<?>, Object> singletons = new ConcurrentHashMap<>();
    private final Map<Class<?>, Class<?>> componentClasses = new HashMap<>();

    public void scan(String... packageNames) throws Exception {
        for (String packageName : packageNames) {
            scanPackage(packageName);
        }
    }

    private void scanPackage(String packageName) throws Exception {
        String path = packageName.replace('.', '/');
        try (var stream = ClassLoader.getSystemClassLoader().getResources(path)) {
            while (stream.hasMoreElements()) {
                var file = new java.io.File(stream.nextElement().toURI());
                for (String className : file.list()) {
                    if (className.endsWith(".class")) {
                        String fullName = packageName + "." + className.replace(".class", "");
                        Class<?> clazz = Class.forName(fullName);
                        if (clazz.isAnnotationPresent(Component.class)) {
                            componentClasses.put(clazz, clazz);
                        }
                    }
                }
            }
        }
    }

    public <T> T getBean(Class<T> clazz) throws Exception {
        return getBean(clazz, (Class<?>) null);
    }

    @SuppressWarnings("unchecked")
    public <T> T getBean(Class<T> clazz, Class<?> parent) throws Exception {
        // Check if it's a component
        if (!componentClasses.containsKey(clazz)) {
            // Find implementing class
            for (Class<?> componentClass : componentClasses.keySet()) {
                if (clazz.isAssignableFrom(componentClass) && !componentClass.equals(clazz)) {
                    return (T) getBean(componentClass, clazz);
                }
            }
            throw new RuntimeException("No component found for: " + clazz.getName());
        }

        // Check scope
        Scope scope = clazz.getAnnotation(Scope.class);
        String scopeName = scope != null ? scope.value() : "singleton";

        if ("singleton".equals(scopeName)) {
            if (singletons.containsKey(clazz)) {
                return (T) singletons.get(clazz);
            }
            
            T instance = createInstance(clazz);
            singletons.put(clazz, instance);
            return instance;
        }

        // Prototype scope
        return createInstance(clazz);
    }

    private <T> T createInstance(Class<T> clazz) throws Exception {
        // Find constructor with @Inject or default constructor
        Constructor<?> injectConstructor = null;
        for (Constructor<?> c : clazz.getConstructors()) {
            if (c.isAnnotationPresent(Inject.class)) {
                injectConstructor = c;
                break;
            }
        }

        if (injectConstructor == null) {
            injectConstructor = clazz.getConstructor();
        }

        // Resolve dependencies
        Object[] params = new Object[injectConstructor.getParameterCount()];
        int i = 0;
        for (Parameter p : injectConstructor.getParameters()) {
            params[i++] = getBean(p.getType());
        }

        @SuppressWarnings("unchecked")
        T instance = (T) injectConstructor.newInstance(params);

        // Field injection
        injectFields(instance);

        // PostConstruct
        invokeLifecycle(instance, PostConstruct.class);

        return instance;
    }

    private <T> void injectFields(T instance) throws Exception {
        for (Field field : instance.getClass().getDeclaredFields()) {
            if (field.isAnnotationPresent(Inject.class)) {
                field.setAccessible(true);
                field.set(instance, getBean(field.getType()));
            }
        }
    }

    private <T> void invokeLifecycle(T instance, Class<? extends Annotation> annotation) throws Exception {
        for (Method method : instance.getClass().getMethods()) {
            if (method.isAnnotationPresent(annotation)) {
                method.invoke(instance);
            }
        }
    }

    public void close() throws Exception {
        for (Object instance : singletons.values()) {
            invokeLifecycle(instance, PreDestroy.class);
        }
        singletons.clear();
    }
}

public class Main {
    public static void main(String[] args) throws Exception {
        Container container = new Container();
        container.scan("com.example"); // Scan current package

        UserService userService = container.getBean(UserService.class);
        userService.createUser("Alice");
        userService.createUser("Bob");

        // Get same singleton instance
        UserService service2 = container.getBean(UserService.class);
        System.out.println("Same instance: " + (userService == service2));

        container.close();
    }
}
