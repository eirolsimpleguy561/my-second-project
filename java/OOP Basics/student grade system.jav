import java.util.*;
import java.util.stream.*;

class Student {
    private String name;
    private Map<String, Double> grades = new LinkedHashMap<>();

    public Student(String name) { this.name = name; }

    public void addGrade(String subject, double mark) {
        grades.put(subject, mark);
    }

    public double getGPA() {
        if (grades.isEmpty()) return 0;
        return grades.values().stream().mapToDouble(Double::doubleValue).average().orElse(0);
    }

    public char getLetterGrade() {
        double gpa = getGPA();
        if (gpa >= 90) return 'A';
        if (gpa >= 80) return 'B';
        if (gpa >= 70) return 'C';
        if (gpa >= 60) return 'D';
        return 'F';
    }

    public String getName() { return name; }
    public Map<String, Double> getGrades() { return grades; }

    @Override
    public String toString() {
        return String.format("%-15s GPA: %5.1f  Grade: %c", name, getGPA(), getLetterGrade());
    }
}

public class Main {
    public static void main(String[] args) {
        List<Student> students = new ArrayList<>();

        Student alice = new Student("Alice");
        alice.addGrade("Math", 92); alice.addGrade("English", 88);
        alice.addGrade("Science", 95); alice.addGrade("History", 85);

        Student bob = new Student("Bob");
        bob.addGrade("Math", 74); bob.addGrade("English", 68);
        bob.addGrade("Science", 71); bob.addGrade("History", 65);

        Student carol = new Student("Carol");
        carol.addGrade("Math", 98); carol.addGrade("English", 94);
        carol.addGrade("Science", 97); carol.addGrade("History", 91);

        students.addAll(Arrays.asList(alice, bob, carol));

        System.out.println("=== Grade Report ===");
        System.out.println("-".repeat(40));
        students.stream()
            .sorted(Comparator.comparingDouble(Student::getGPA).reversed())
            .forEach(System.out::println);

        Student top = students.stream().max(Comparator.comparingDouble(Student::getGPA)).get();
        Student low = students.stream().min(Comparator.comparingDouble(Student::getGPA)).get();
        double classAvg = students.stream().mapToDouble(Student::getGPA).average().orElse(0);

        System.out.println("-".repeat(40));
        System.out.printf("Class Average : %.1f%n", classAvg);
        System.out.println("Top Student   : " + top.getName() + " (" + top.getGPA() + ")");
        System.out.println("Needs Help    : " + low.getName() + " (" + low.getGPA() + ")");
    }
}
