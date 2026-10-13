import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;
import java.util.stream.Collectors;

class Book {
    private String title, author, isbn;
    private boolean available;

    public Book(String title, String author, String isbn) {
        this.title = title; this.author = author;
        this.isbn = isbn; this.available = true;
    }

    public boolean isAvailable() { return available; }
    public void setAvailable(boolean available) { this.available = available; }
    public String getTitle() { return title; }
    public String getAuthor() { return author; }
    public String getIsbn() { return isbn; }

    @Override
    public String toString() {
        return String.format("%-30s %-20s %-15s %s",
            title, author, isbn, available ? "Available" : "Borrowed");
    }
}

class Library {
    private List<Book> books = new ArrayList<>();

    public void addBook(Book book) {
        books.add(book);
        System.out.println("Added: " + book.getTitle());
    }

    public List<Book> search(String query) {
        String q = query.toLowerCase();
        return books.stream()
            .filter(b -> b.getTitle().toLowerCase().contains(q)
                      || b.getAuthor().toLowerCase().contains(q))
            .collect(Collectors.toList());
    }

    public boolean borrow(String isbn) {
        for (Book b : books) {
            if (b.getIsbn().equals(isbn) && b.isAvailable()) {
                b.setAvailable(false); return true;
            }
        }
        return false;
    }

    public boolean returnBook(String isbn) {
        for (Book b : books) {
            if (b.getIsbn().equals(isbn) && !b.isAvailable()) {
                b.setAvailable(true); return true;
            }
        }
        return false;
    }

    public void displayAll() {
        System.out.printf("%-30s %-20s %-15s %s%n", "Title", "Author", "ISBN", "Status");
        System.out.println("-".repeat(75));
        books.forEach(System.out::println);
        long avail = books.stream().filter(Book::isAvailable).count();
        System.out.println("\nTotal: " + books.size() + " | Available: " + avail);
    }
}

public class Main {
    public static void main(String[] args) {
        Library lib = new Library();
        lib.addBook(new Book("Clean Code", "Robert C. Martin", "978-0132350884"));
        lib.addBook(new Book("Effective Java", "Joshua Bloch", "978-0134685991"));
        lib.addBook(new Book("The Pragmatic Programmer", "Andrew Hunt", "978-0135957059"));
        lib.addBook(new Book("Design Patterns", "Gang of Four", "978-0201633610"));

        System.out.println("\n=== Library Catalog ===");
        lib.displayAll();

        System.out.println("\nBorrowing 'Effective Java'...");
        lib.borrow("978-0134685991");

        System.out.println("\nSearch results for 'java':");
        lib.search("java").forEach(System.out::println);

        lib.displayAll();
    }
}
