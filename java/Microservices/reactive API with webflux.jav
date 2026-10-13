// === pom.xml dependencies ===
// spring-boot-starter-webflux, spring-boot-starter-data-mongodb-reactive

// === User.java ===
package com.example.reactive;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Document
public class User {
    @Id
    private String id;
    private String name;
    private String email;
    private int age;

    // Constructors, getters, setters
    public User() {}
    public User(String name, String email, int age) {
        this.name = name;
        this.email = email;
        this.age = age;
    }
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public int getAge() { return age; }
    public void setAge(int age) { this.age = age; }
}

// === UserRepository.java ===
package com.example.reactive;

import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import reactor.core.publisher.Flux;

public interface UserRepository extends ReactiveMongoRepository<User, String> {
    Flux<User> findByAgeGreaterThan(int age);
}

// === UserController.java (Annotation-based) ===
package com.example.reactive;

import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import org.springframework.http.MediaType;
import java.time.Duration;

@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserRepository repository;

    public UserController(UserRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public Flux<User> getAll() {
        return repository.findAll();
    }

    @GetMapping("/{id}")
    public Mono<User> getById(@PathVariable String id) {
        return repository.findById(id);
    }

    @PostMapping
    public Mono<User> create(@RequestBody User user) {
        return repository.save(user);
    }

    @PutMapping("/{id}")
    public Mono<User> update(@PathVariable String id, @RequestBody User user) {
        return repository.findById(id)
            .flatMap(existing -> {
                existing.setName(user.getName());
                existing.setEmail(user.getEmail());
                existing.setAge(user.getAge());
                return repository.save(existing);
            });
    }

    @DeleteMapping("/{id}")
    public Mono<Void> delete(@PathVariable String id) {
        return repository.deleteById(id);
    }

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<User> streamUsers() {
        return repository.findAll()
            .delayElements(Duration.ofSeconds(1))
            .repeat(); // Infinite stream
    }

    @GetMapping("/age/{min}")
    public Flux<User> getByAge(@PathVariable int min) {
        return repository.findByAgeGreaterThan(min);
    }
}

// === UserRouter.java (Functional Routing) ===
package com.example.reactive;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.*;
import reactor.core.publisher.Mono;

@Configuration
public class UserRouter {
    @Bean
    public RouterFunction<ServerResponse> route(UserHandler handler) {
        return RouterFunctions
            .route(RequestPredicates.GET("/api/users"), handler::getAll)
            .andRoute(RequestPredicates.GET("/api/users/{id}"), handler::getById)
            .andRoute(RequestPredicates.POST("/api/users"), handler::create)
            .andRoute(RequestPredicates.PUT("/api/users/{id}"), handler::update)
            .andRoute(RequestPredicates.DELETE("/api/users/{id}"), handler::delete);
    }
}

@Component
class UserHandler {
    private final UserRepository repository;

    public UserHandler(UserRepository repository) {
        this.repository = repository;
    }

    public Mono<ServerResponse> getAll(ServerRequest request) {
        return ServerResponse.ok().body(repository.findAll(), User.class);
    }

    public Mono<ServerResponse> getById(ServerRequest request) {
        String id = request.pathVariable("id");
        return repository.findById(id)
            .flatMap(user -> ServerResponse.ok().bodyValue(user))
            .switchIfEmpty(ServerResponse.notFound().build());
    }

    public Mono<ServerResponse> create(ServerRequest request) {
        return request.bodyToMono(User.class)
            .flatMap(repository::save)
            .flatMap(user -> ServerResponse.ok().bodyValue(user));
    }

    public Mono<ServerResponse> update(ServerRequest request) {
        String id = request.pathVariable("id");
        return request.bodyToMono(User.class)
            .flatMap(user -> repository.findById(id)
                .flatMap(existing -> {
                    existing.setName(user.getName());
                    existing.setEmail(user.getEmail());
                    existing.setAge(user.getAge());
                    return repository.save(existing);
                }))
            .flatMap(user -> ServerResponse.ok().bodyValue(user))
            .switchIfEmpty(ServerResponse.notFound().build());
    }

    public Mono<ServerResponse> delete(ServerRequest request) {
        String id = request.pathVariable("id");
        return repository.deleteById(id)
            .then(ServerResponse.noContent().build());
    }
}

// === WebClient example ===
package com.example.reactive;

import org.springframework.web.reactive.function.client.WebClient;

public class WebClientExample {
    public static void main(String[] args) {
        WebClient client = WebClient.create("http://localhost:8080");
        
        // Non-blocking request
        client.get()
            .uri("/api/users")
            .retrieve()
            .bodyToFlux(User.class)
            .take(5)
            .subscribe(System.out::println);
    }
}
