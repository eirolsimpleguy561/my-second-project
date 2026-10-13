// === pom.xml dependencies ===
// graphql-spring-boot-starter, graphql-java-tools, graphiql-spring-boot-starter

// === schema.graphqls ===
type Book {
    id: ID!
    title: String!
    author: String!
    isbn: String!
    available: Boolean!
}

type Query {
    books(available: Boolean): [Book!]!
    book(id: ID!): Book
}

type Mutation {
    addBook(title: String!, author: String!, isbn: String!): Book!
    borrowBook(id: ID!): Book!
    returnBook(id: ID!): Book!
}

type Subscription {
    bookAdded: Book!
}

// === Book.java ===
package com.example.graphql;

public class Book {
    private String id;
    private String title;
    private String author;
    private String isbn;
    private boolean available;

    public Book(String id, String title, String author, String isbn) {
        this.id = id;
        this.title = title;
        this.author = author;
        this.isbn = isbn;
        this.available = true;
    }

    // Getters and Setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getAuthor() { return author; }
    public void setAuthor(String author) { this.author = author; }
    public String getIsbn() { return isbn; }
    public void setIsbn(String isbn) { this.isbn = isbn; }
    public boolean isAvailable() { return available; }
    public void setAvailable(boolean available) { this.available = available; }
}

// === QueryResolver.java ===
package com.example.graphql;

import graphql.kickstart.tools.GraphQLQueryResolver;
import org.springframework.stereotype.Component;
import java.util.*;
import java.util.stream.Collectors;

@Component
public class QueryResolver implements GraphQLQueryResolver {
    private final BookService bookService;

    public QueryResolver(BookService bookService) {
        this.bookService = bookService;
    }

    public List<Book> books(Boolean available) {
        return bookService.getAllBooks();
    }

    public Book book(String id) {
        return bookService.getBook(id);
    }
}

// === MutationResolver.java ===
package com.example.graphql;

import graphql.kickstart.tools.GraphQLMutationResolver;
import org.springframework.stereotype.Component;

@Component
public class MutationResolver implements GraphQLMutationResolver {
    private final BookService bookService;

    public MutationResolver(BookService bookService) {
        this.bookService = bookService;
    }

    public Book addBook(String title, String author, String isbn) {
        return bookService.addBook(title, author, isbn);
    }

    public Book borrowBook(String id) {
        return bookService.borrowBook(id);
    }

    public Book returnBook(String id) {
        return bookService.returnBook(id);
    }
}

// === SubscriptionResolver.java ===
package com.example.graphql;

import graphql.kickstart.tools.GraphQLSubscriptionResolver;
import org.reactivestreams.Publisher;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class SubscriptionResolver implements GraphQLSubscriptionResolver {
    private final List<Flux<Book>> subscriptions = new ArrayList<>();

    public Publisher<Book> bookAdded() {
        // Simulate book additions
        return Flux.interval(Duration.ofSeconds(10))
            .map(i -> new Book(
                UUID.randomUUID().toString(),
                "New Book " + i,
                "Author " + i,
                "ISBN-" + i
            ));
    }
}

// === BookService.java ===
package com.example.graphql;

import org.springframework.stereotype.Service;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class BookService {
    private final Map<String, Book> books = new ConcurrentHashMap<>();

    public BookService() {
        // Seed some books
        addBook("Clean Code", "Robert C. Martin", "978-0132350884");
        addBook("Effective Java", "Joshua Bloch", "978-0134685991");
    }

    public Book addBook(String title, String author, String isbn) {
        String id = UUID.randomUUID().toString();
        Book book = new Book(id, title, author, isbn);
        books.put(id, book);
        return book;
    }

    public List<Book> getAllBooks() {
        return new ArrayList<>(books.values());
    }

    public Book getBook(String id) {
        return books.get(id);
    }

    public Book borrowBook(String id) {
        Book book = books.get(id);
        if (book != null && book.isAvailable()) {
            book.setAvailable(false);
            return book;
        }
        throw new RuntimeException("Book not available");
    }

    public Book returnBook(String id) {
        Book book = books.get(id);
        if (book != null && !book.isAvailable()) {
            book.setAvailable(true);
            return book;
        }
        throw new RuntimeException("Book not borrowed");
    }
}

// GraphiQL available at: http://localhost:8080/graphiql
// Query example:
// query { books { title author available } }
// Mutation example:
// mutation { addBook(title: "Java 101", author: "John Doe", isbn: "1234567890") { id } }
