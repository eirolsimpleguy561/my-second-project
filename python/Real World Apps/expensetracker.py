import csv
import os
from datetime import datetime
from collections import defaultdict

class ExpenseTracker:
    def __init__(self, filename="expenses.csv"):
        self.filename = filename
        self.categories = ["Food", "Transport", "Entertainment", "Bills", "Shopping", "Health", "Other"]
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Amount", "Category", "Description"])
    
    def add_expense(self, amount, category, description=""):
        date = datetime.now().strftime("%Y-%m-%d")
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date, amount, category, description])
        print(f"Expense added: ${amount} - {category}")
    
    def get_expenses(self, start_date=None, end_date=None, category=None):
        expenses = []
        with open(self.filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = datetime.strptime(row["Date"], "%Y-%m-%d")
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue
                if category and row["Category"].lower() != category.lower():
                    continue
                expenses.append(row)
        return expenses
    
    def show_summary(self):
        expenses = self.get_expenses()
        if not expenses:
            print("No expenses recorded.")
            return
        
        total = sum(float(e["Amount"]) for e in expenses)
        by_category = defaultdict(float)
        by_month = defaultdict(float)
        
        for e in expenses:
            by_category[e["Category"]] += float(e["Amount"])
            month = datetime.strptime(e["Date"], "%Y-%m-%d").strftime("%Y-%m")
            by_month[month] += float(e["Amount"])
        
        print(f"\n{'='*50}")
        print(f"Total Expenses: ${total:.2f}")
        print(f"Number of Transactions: {len(expenses)}")
        print(f"{'='*50}")
        
        print("\nBy Category:")
        for cat in self.categories:
            if cat in by_category:
                percentage = (by_category[cat] / total) * 100
                print(f"  {cat:<15}: ${by_category[cat]:>8.2f} ({percentage:>5.1f}%)")
        
        print("\nMonthly Summary:")
        for month in sorted(by_month.keys()):
            print(f"  {month}: ${by_month[month]:.2f}")
    
    def export_report(self, filename):
        expenses = self.get_expenses()
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["Date", "Amount", "Category", "Description"])
            writer.writeheader()
            writer.writerows(expenses)
        print(f"Report exported to {filename}")
    
    def run(self):
        print("=== Expense Tracker ===")
        
        while True:
            print("\n1. Add Expense")
            print("2. View All Expenses")
            print("3. Show Summary")
            print("4. Export Report")
            print("5. Exit")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                try:
                    amount = float(input("Amount: $"))
                    print(f"Categories: {', '.join(self.categories)}")
                    category = input("Category: ").strip().capitalize()
                    if category not in self.categories:
                        category = "Other"
                    description = input("Description (optional): ").strip()
                    self.add_expense(amount, category, description)
                except ValueError:
                    print("Invalid amount.")
            
            elif choice == '2':
                expenses = self.get_expenses()
                if expenses:
                    print(f"\n{'Date':<12} {'Amount':<8} {'Category':<15} {'Description'}")
                    print("-" * 50)
                    for e in expenses:
                        print(f"{e['Date']:<12} ${float(e['Amount']):<7.2f} {e['Category']:<15} {e['Description']}")
                else:
                    print("No expenses found.")
            
            elif choice == '3':
                self.show_summary()
            
            elif choice == '4':
                filename = input("Export filename (CSV): ").strip()
                if not filename.endswith('.csv'):
                    filename += '.csv'
                self.export_report(filename)
            
            elif choice == '5':
                print("Goodbye!")
                break

if __name__ == "__main__":
    tracker = ExpenseTracker()
    tracker.run()
