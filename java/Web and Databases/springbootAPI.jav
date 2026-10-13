// === pom.xml dependencies (Spring Boot 3.x) ===
// spring-boot-starter-web, spring-boot-starter-data-jpa,
// spring-boot-starter-validation, h2, springdoc-openapi-starter-webmvc-ui

// === Task.java (Entity) ===
package com.example.tasks;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;

@Entity
public class Task {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "Title is required")
    private String title;

    private String description;
    private boolean completed = false;

    // Getters & Setters
    public Long getId() { return id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getDescription() { return description; }
    public void setDescription(String desc) { this.description = desc; }
    public boolean isCompleted() { return completed; }
    public void setCompleted(boolean completed) { this.completed = completed; }
}

// === TaskRepository.java ===
package com.example.tasks;
import org.springframework.data.jpa.repository.JpaRepository;
public interface TaskRepository extends JpaRepository<Task, Long> {}

// === TaskController.java ===
package com.example.tasks;

import jakarta.validation.Valid;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/tasks")
public class TaskController {
    private final TaskRepository repo;
    public TaskController(TaskRepository repo) { this.repo = repo; }

    @GetMapping
    public List<Task> getAll() { return repo.findAll(); }

    @PostMapping
    public ResponseEntity<Task> create(@Valid @RequestBody Task task) {
        return ResponseEntity.status(HttpStatus.CREATED).body(repo.save(task));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Task> getById(@PathVariable Long id) {
        return repo.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PutMapping("/{id}")
    public ResponseEntity<Task> update(@PathVariable Long id, @Valid @RequestBody Task updated) {
        return repo.findById(id).map(task -> {
            task.setTitle(updated.getTitle());
            task.setDescription(updated.getDescription());
            task.setCompleted(updated.isCompleted());
            return ResponseEntity.ok(repo.save(task));
        }).orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        if (!repo.existsById(id)) return ResponseEntity.notFound().build();
        repo.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}

// Run: mvn spring-boot:run
// Swagger UI: http://localhost:8080/swagger-ui.html
