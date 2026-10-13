import random
import string
import sys

def generate_password(length=12, use_upper=True, use_digits=True, use_symbols=True):
    characters = string.ascii_lowercase
    if use_upper:
        characters += string.ascii_uppercase
    if use_digits:
        characters += string.digits
    if use_symbols:
        characters += string.punctuation
    
    if not characters:
        return "Error: No character types selected"
    
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def check_strength(password):
    score = 0
    if len(password) >= 12:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1
    
    if score == 4:
        return "Strong"
    elif score >= 2:
        return "Medium"
    else:
        return "Weak"

def main():
    print("=== Password Generator ===")
    
    while True:
        try:
            length = int(input("Password length (8-32): "))
            if 8 <= length <= 32:
                break
            print("Please enter a length between 8 and 32.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    use_upper = input("Include uppercase letters? (y/n): ").lower() == 'y'
    use_digits = input("Include digits? (y/n): ").lower() == 'y'
    use_symbols = input("Include symbols? (y/n): ").lower() == 'y'
    
    password = generate_password(length, use_upper, use_digits, use_symbols)
    strength = check_strength(password)
    
    print(f"\nGenerated Password: {password}")
    print(f"Password Strength: {strength}")
    
    if strength != "Strong":
        print("\nTip: Include more character types and increase length for a stronger password.")

if __name__ == "__main__":
    main()
