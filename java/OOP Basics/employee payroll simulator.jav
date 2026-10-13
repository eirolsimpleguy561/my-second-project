import java.util.*;

interface Payable {
    double calculateSalary();
    void generatePaySlip();
}

abstract class Employee implements Payable {
    protected String name;
    protected String id;
    protected String department;

    public Employee(String name, String id, String department) {
        this.name = name; this.id = id; this.department = department;
    }
}

class FullTimeEmployee extends Employee {
    private double monthlySalary;

    public FullTimeEmployee(String name, String id, String dept, double salary) {
        super(name, id, dept);
        this.monthlySalary = salary;
    }

    @Override
    public double calculateSalary() {
        return monthlySalary - (monthlySalary * 0.2); // 20% tax
    }

    @Override
    public void generatePaySlip() {
        System.out.printf("Pay Slip for %s: $%.2f\n", name, calculateSalary());
    }
}

class PartTimeEmployee extends Employee {
    private double hourlyRate;
    private int hoursWorked;

    public PartTimeEmployee(String name, String id, String dept, double rate, int hours) {
        super(name, id, dept);
        this.hourlyRate = rate;
        this.hoursWorked = hours;
    }

    @Override
    public double calculateSalary() {
        return hourlyRate * hoursWorked;
    }

    @Override
    public void generatePaySlip() {
        System.out.printf("Pay Slip for %s: $%.2f\n", name, calculateSalary());
    }
}

public class Main {
    public static void main(String[] args) {
        List<Employee> employees = new ArrayList<>();
        employees.add(new FullTimeEmployee("John", "FT001", "IT", 5000));
        employees.add(new PartTimeEmployee("Alice", "PT001", "HR", 20, 30));
        
        employees.forEach(Employee::generatePaySlip);
    }
}
