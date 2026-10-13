import re

def is_palindrome(text):
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    return cleaned == cleaned[::-1], cleaned

def longest_palindrome_substring(text):
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    n = len(cleaned)
    longest = ""
    
    for i in range(n):
        for j in range(i, n):
            substring = cleaned[i:j+1]
            if substring == substring[::-1] and len(substring) > len(longest):
                longest = substring
    
    return longest

def main():
    print("=== Palindrome Checker ===")
    print("Check if a word, phrase, or number is a palindrome.")
    
    while True:
        text = input("\nEnter text to check (or 'exit' to quit): ").strip()
        
        if text.lower() == 'exit':
            print("Goodbye!")
            break
        
        if not text:
            print("Please enter some text.")
            continue
        
        is_pal, cleaned = is_palindrome(text)
        
        print(f"\nOriginal: {text}")
        print(f"Cleaned: {cleaned if cleaned else '(empty)'}")
        
        if is_pal:
            print("✓ This IS a palindrome! ✓")
        else:
            print("✗ This is NOT a palindrome. ✗")
        
        if len(cleaned) > 1:
            longest = longest_palindrome_substring(text)
            if longest and len(longest) > 1:
                print(f"Longest palindrome substring: '{longest}' (length {len(longest)})")
        
        try:
            num = int(text)
            binary = bin(num)[2:]
            is_binary_pal, _ = is_palindrome(binary)
            if is_binary_pal:
                print(f"In binary ({binary}), this number is also a palindrome!")
        except ValueError:
            pass

if __name__ == "__main__":
    main()
