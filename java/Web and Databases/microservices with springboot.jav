// === pom.xml (Service Discovery) ===
// spring-cloud-starter-netflix-eureka-server

// === EurekaServerApplication.java ===
package com.example.discovery;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}

// === pom.xml (Product Service) ===
// spring-boot-starter-web, spring-cloud-starter-netflix-eureka-client
// spring-boot-starter-data-jpa, h2, spring-cloud-starter-circuitbreaker-resilience4j

// === ProductServiceApplication.java ===
package com.example.product;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class ProductServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(ProductServiceApplication.class, args);
    }
}

// === Product.java ===
package com.example.product;

import javax.persistence.*;

@Entity
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    private double price;
    private int quantity;

    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public double getPrice() { return price; }
    public void setPrice(double price) { this.price = price; }
    public int getQuantity() { return quantity; }
    public void setQuantity(int quantity) { this.quantity = quantity; }
}

// === ProductController.java ===
package com.example.product;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductRepository repository;

    public ProductController(ProductRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public List<Product> getAll() {
        return repository.findAll();
    }

    @GetMapping("/{id}")
    public Product getById(@PathVariable Long id) {
        return repository.findById(id).orElseThrow();
    }

    @PostMapping
    public Product create(@RequestBody Product product) {
        return repository.save(product);
    }

    @PutMapping("/{id}/stock")
    public Product updateStock(@PathVariable Long id, @RequestParam int quantity) {
        Product product = getById(id);
        product.setQuantity(quantity);
        return repository.save(product);
    }
}

// === OrderService Client ===
package com.example.product;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.*;

@FeignClient(name = "order-service")
public interface OrderServiceClient {
    @PostMapping("/api/orders")
    Object createOrder(@RequestBody Map<String, Object> order);
}

// === pom.xml (API Gateway) ===
// spring-cloud-starter-gateway, spring-cloud-starter-netflix-eureka-client

// === GatewayApplication.java ===
package com.example.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
@EnableDiscoveryClient
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }

    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("product_route", r -> r
                .path("/api/products/**")
                .filters(f -> f
                    .circuitBreaker(config -> config
                        .setName("productCB")
                        .setFallbackUri("forward:/fallback/products"))
                    .retry(config -> config
                        .setRetries(3)
                        .setStatuses(HttpStatus.SERVICE_UNAVAILABLE)))
                .uri("lb://product-service"))
            .route("order_route", r -> r
                .path("/api/orders/**")
                .uri("lb://order-service"))
            .build();
    }
}

// === FallbackController.java ===
package com.example.gateway;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/fallback")
public class FallbackController {
    @GetMapping("/products")
    public Map<String, String> productFallback() {
        return Map.of("message", "Product service is currently unavailable. Please try again later.");
    }
}

// === application.yml (Product Service) ===
spring:
  application:
    name: product-service
  datasource:
    url: jdbc:h2:mem:productdb
    driver-class-name: org.h2.Driver
  h2:
    console:
      enabled: true

server:
  port: 8081

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/

resilience4j:
  circuitbreaker:
    instances:
      orderService:
        sliding-window-size: 10
        failure-rate-threshold: 50
        wait-duration-in-open-state: 5000

// === Startup Sequence ===
// 1. Run EurekaServerApplication (port 8761)
// 2. Run ProductServiceApplication (port 8081)
// 3. Run GatewayApplication (port 8080)
// 4. Access: http://localhost:8080/api/products
// 5. Eureka Dashboard: http://localhost:8761
