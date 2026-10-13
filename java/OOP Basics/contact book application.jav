import java.util.*;

class Contact {
    private String name, phone, email, address;

    public Contact(String name, String phone, String email, String address) {
        this.name = name; this.phone = phone;
        this.email = email; this.address = address;
    }

    @Override
    public String toString() {
        return String.format("Name: %s, Phone: %s, Email: %s, Address: %s",
            name, phone, email, address);
    }

    public String getName() { return name; }
    public void setPhone(String phone) { this.phone = phone; }
    public void setEmail(String email) { this.email = email; }
    public void setAddress(String address) { this.address = address; }
}

class ContactBook {
    private Map<String, Contact> contacts = new HashMap<>();

    public void addContact(Contact contact) {
        contacts.put(contact.getName().toLowerCase(), contact);
    }

    public Contact searchContact(String name) {
        return contacts.get(name.toLowerCase());
    }

    public boolean deleteContact(String name) {
        return contacts.remove(name.toLowerCase()) != null;
    }

    public void displayAll() {
        List<Contact> sorted = new ArrayList<>(contacts.values());
        sorted.sort(Comparator.comparing(Contact::getName));
        sorted.forEach(System.out::println);
    }
}

public class Main {
    public static void main(String[] args) {
        ContactBook book = new ContactBook();
        book.addContact(new Contact("Alice", "123-456-7890", "alice@email.com", "123 Main St"));
        book.addContact(new Contact("Bob", "987-654-3210", "bob@email.com", "456 Oak Ave"));
        
        System.out.println("Searching for Alice:");
        System.out.println(book.searchContact("Alice"));
        
        System.out.println("\nAll Contacts:");
        book.displayAll();
    }
}
