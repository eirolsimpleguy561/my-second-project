import random
import string

class SimpleEncryption:
    def __init__(self):
        self.alphabet = string.ascii_lowercase
    
    def caesar_encrypt(self, text, shift):
        result = ""
        for char in text.lower():
            if char in self.alphabet:
                idx = (self.alphabet.index(char) + shift) % 26
                result += self.alphabet[idx]
            else:
                result += char
        return result
    
    def caesar_decrypt(self, text, shift):
        return self.caesar_encrypt(text, -shift)
    
    def caesar_brute_force(self, encrypted_text):
        print("\nBrute force results:")
        for shift in range(26):
            decrypted = self.caesar_decrypt(encrypted_text, shift)
            print(f"Shift {shift:2}: {decrypted[:50]}")
    
    def generate_substitution_key(self):
        shuffled = list(self.alphabet)
        random.shuffle(shuffled)
        return dict(zip(self.alphabet, shuffled))
    
    def substitution_encrypt(self, text, key):
        return ''.join(key.get(c, c) for c in text.lower())
    
    def substitution_decrypt(self, text, key):
        reverse_key = {v: k for k, v in key.items()}
        return ''.join(reverse_key.get(c, c) for c in text.lower())
    
    def run(self):
        print("=== Simple Encryption Tool ===")
        
        while True:
            print("\n1. Caesar Cipher")
            print("2. Caesar Cipher Brute Force")
            print("3. Substitution Cipher")
            print("4. Exit")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                text = input("Enter message: ").strip()
                try:
                    shift = int(input("Enter shift key (1-25): "))
                    encrypted = self.caesar_encrypt(text, shift)
                    print(f"Encrypted: {encrypted}")
                    decrypted = self.caesar_decrypt(encrypted, shift)
                    print(f"Decrypted: {decrypted}")
                except ValueError:
                    print("Invalid shift key.")
            
            elif choice == '2':
                encrypted = input("Enter encrypted message: ").strip()
                self.caesar_brute_force(encrypted)
            
            elif choice == '3':
                text = input("Enter message: ").strip()
                key = self.generate_substitution_key()
                print(f"Key: {key}")
                encrypted = self.substitution_encrypt(text, key)
                print(f"Encrypted: {encrypted}")
                decrypted = self.substitution_decrypt(encrypted, key)
                print(f"Decrypted: {decrypted}")
            
            elif choice == '4':
                print("Goodbye!")
                break

if __name__ == "__main__":
    tool = SimpleEncryption()
    tool.run()
