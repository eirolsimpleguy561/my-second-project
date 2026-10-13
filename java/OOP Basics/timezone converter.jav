import java.time.*;
import java.time.format.*;
import java.util.*;

public class Main {
    private static final Map<String, String> TIMEZONES = new HashMap<>();
    static {
        TIMEZONES.put("EST", "America/New_York");
        TIMEZONES.put("PST", "America/Los_Angeles");
        TIMEZONES.put("UTC", "UTC");
        TIMEZONES.put("IST", "Asia/Kolkata");
        TIMEZONES.put("JST", "Asia/Tokyo");
    }

    public static void convertTime(String fromZone, String toZone, LocalDateTime dateTime) {
        ZoneId fromId = ZoneId.of(TIMEZONES.get(fromZone));
        ZoneId toId = ZoneId.of(TIMEZONES.get(toZone));

        ZonedDateTime zdt = ZonedDateTime.of(dateTime, fromId);
        ZonedDateTime converted = zdt.withZoneSameInstant(toId);

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        System.out.println("From " + fromZone + ": " + zdt.format(formatter));
        System.out.println("To " + toZone + ": " + converted.format(formatter));
    }

    public static void main(String[] args) {
        LocalDateTime now = LocalDateTime.now();
        System.out.println("Current time: " + now);
        convertTime("EST", "IST", now);
        
        // Show current times in different zones
        System.out.println("\nCurrent times:");
        TIMEZONES.keySet().forEach(zone -> {
            ZonedDateTime zdt = ZonedDateTime.now(ZoneId.of(TIMEZONES.get(zone)));
            System.out.println(zone + ": " + zdt.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        });
    }
}
