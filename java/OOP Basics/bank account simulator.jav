import java.util.*;

abstract class BankAccount {
    private String accountNumber;
    private double balance;
    private List<String> transactions = new ArrayList<>();

    public BankAccount(String accountNumber) {
        this.accountNumber = accountNumber;
        this.balance = 0.0;
    }

    public void deposit(double amount) {
        balance += amount;
        transactions.add("Deposited: $" + amount);
    }

    public boolean withdraw(double amount) {
        if (balance >= amount) {
            balance -= amount;
            transactions.add("Withdrew: $" + amount);
            return true;
        }
        return false;
    }

    public void displayTransactions() {
        transactions.forEach(System.out::println);
    }

    public double getBalance() { return balance; }
    public String getAccountNumber() { return accountNumber; }
    public abstract double calculateInterest();
}

class SavingsAccount extends BankAccount {
    private double interestRate = 0.05;

    public SavingsAccount(String accountNumber) {
        super(accountNumber);
    }

    @Override
    public double calculateInterest() {
        return getBalance() * interestRate;
    }
}

class CheckingAccount extends BankAccount {
    private double overdraftLimit = 500;

    public CheckingAccount(String accountNumber) {
        super(accountNumber);
    }

    @Override
    public boolean withdraw(double amount) {
        if (getBalance() + overdraftLimit >= amount) {
            super.withdraw(amount);
            return true;
        }
        return false;
    }

    @Override
    public double calculateInterest() {
        return 0; // No interest for checking accounts
    }
}

public class Main {
    public static void main(String[] args) {
        SavingsAccount sa = new SavingsAccount("SA001");
        CheckingAccount ca = new CheckingAccount("CA001");

        sa.deposit(1000);
        ca.deposit(500);

        sa.withdraw(200);
        ca.withdraw(800);

        System.out.println("Savings Account Interest: $" + sa.calculateInterest());
        System.out.println("Checking Balance: $" + ca.getBalance());
    }
}
