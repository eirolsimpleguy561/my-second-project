import json
import os

CONTACTS_FILE = "contacts.json"

def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return []
    with open(CONTACTS_FILE, 'r') as f:
        return json.load(f)

def save_contacts(contacts):
    with open(CONTACTS_FILE, 'w') as f:
        json.dump(contacts, f, indent=2)

def display_contacts(contacts):
    if not contacts:
        print("\nNo contacts found.")
        return
    
    print("\n" + "="*80)
    print(f"{'ID':<4} {'Name':<20} {'Phone':<15} {'Email':<25} {'Address':<15}")
    print("-"*80)
    for i, contact in enumerate(contacts, 1):
        print(f"{i:<4} {contact['name'][:20]:<20} {contact['phone'][:15]:<15} "
              f"{contact['email'][:25]:<25} {contact['address'][:15]:<15}")
    print("="*80)

def add_contact(contacts):
    print("\n=== Add New Contact ===")
    name = input("Name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    
    phone = input("Phone: ").strip()
    email = input("Email: ").strip()
    address = input("Address: ").strip()
    
    contacts.append({
        "name": name,
        "phone": phone,
        "email": email,
        "address": address
    })
    save_contacts(contacts)
    print(f"Contact '{name}' added successfully!")

def search_contacts(contacts):
    search_term = input("Enter name or phone to search: ").strip().lower()
    results = [c for c in contacts 
               if search_term in c['name'].lower() or search_term in c['phone']]
    
    if results:
        display_contacts(results)
    else:
        print("No matching contacts found.")

def update_contact(contacts):
    display_contacts(contacts)
    try:
        index = int(input("Enter contact ID to update: ")) - 1
        if 0 <= index < len(contacts):
            contact = contacts[index]
            print(f"Updating contact: {contact['name']}")
            
            name = input(f"Name ({contact['name']}): ").strip()
            if name:
                contact['name'] = name
            
            phone = input(f"Phone ({contact['phone']}): ").strip()
            if phone:
                contact['phone'] = phone
            
            email = input(f"Email ({contact['email']}): ").strip()
            if email:
                contact['email'] = email
            
            address = input(f"Address ({contact['address']}): ").strip()
            if address:
                contact['address'] = address
            
            save_contacts(contacts)
            print("Contact updated successfully!")
        else:
            print("Invalid contact ID.")
    except ValueError:
        print("Invalid input.")

def delete_contact(contacts):
    display_contacts(contacts)
    try:
        index = int(input("Enter contact ID to delete: ")) - 1
        if 0 <= index < len(contacts):
            deleted = contacts.pop(index)
            save_contacts(contacts)
            print(f"Contact '{deleted['name']}' deleted successfully!")
        else:
            print("Invalid contact ID.")
    except ValueError:
        print("Invalid input.")

def main():
    contacts = load_contacts()
    
    while True:
        print("\n=== Contact Book ===")
        print("1. View All Contacts")
        print("2. Add Contact")
        print("3. Search Contacts")
        print("4. Update Contact")
        print("5. Delete Contact")
        print("6. Exit")
        
        choice = input("Choose option (1-6): ").strip()
        
        if choice == '1':
            display_contacts(contacts)
        elif choice == '2':
            add_contact(contacts)
        elif choice == '3':
            search_contacts(contacts)
        elif choice == '4':
            update_contact(contacts)
        elif choice == '5':
            delete_contact(contacts)
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose 1-6.")

if __name__ == "__main__":
    main()
