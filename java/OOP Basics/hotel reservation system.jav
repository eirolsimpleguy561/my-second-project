import java.util.*;

class Room {
    private int number;
    private String type; // single, double, suite
    private double rate;
    private boolean booked;

    public Room(int number, String type, double rate) {
        this.number = number;
        this.type = type;
        this.rate = rate;
        this.booked = false;
    }

    public boolean isAvailable() { return !booked; }
    public void bookRoom() { booked = true; }
    public void checkout() { booked = false; }
    public double getRate() { return rate; }
    
    @Override
    public String toString() {
        return String.format("Room %d: %s (Rate: $%.2f, %s)", 
            number, type, rate, booked ? "Booked" : "Available");
    }
}

class Hotel {
    private Map<Integer, Room> rooms = new HashMap<>();
    private Map<String, Integer> bookings = new HashMap<>(); // customer name -> room number

    public void addRoom(Room room) {
        rooms.put(room.getNumber(), room);
    }

    public List<Room> searchAvailable() {
        return rooms.values().stream()
            .filter(Room::isAvailable)
            .collect(Collectors.toList());
    }

    public boolean bookRoom(int roomNumber, String customer) {
        Room room = rooms.get(roomNumber);
        if (room != null && room.isAvailable()) {
            room.bookRoom();
            bookings.put(customer, roomNumber);
            return true;
        }
        return false;
    }

    public boolean checkout(String customer) {
        Integer roomNumber = bookings.remove(customer);
        if (roomNumber != null) {
            rooms.get(roomNumber).checkout();
            return true;
        }
        return false;
    }

    public void displayRooms() {
        rooms.values().forEach(System.out::println);
    }
}

public class Main {
    public static void main(String[] args) {
        Hotel hotel = new Hotel();
        hotel.addRoom(new Room(101, "single", 100));
        hotel.addRoom(new Room(102, "double", 150));
        hotel.addRoom(new Room(103, "suite", 250));

        System.out.println("Available rooms:");
        hotel.searchAvailable().forEach(System.out::println);

        hotel.bookRoom(101, "John Smith");
        hotel.bookRoom(102, "Jane Doe");

        System.out.println("\nAfter booking:");
        hotel.displayRooms();

        hotel.checkout("John Smith");
        System.out.println("\nAfter checkout:");
        hotel.displayRooms();
    }
}
