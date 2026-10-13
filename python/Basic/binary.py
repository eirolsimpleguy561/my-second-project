class BinaryConverter:
    def decimal_to_binary(self, n):
        if n == 0:
            return "0"
        is_negative = n < 0
        n = abs(n)
        binary = ""
        while n > 0:
            binary = str(n % 2) + binary
            n //= 2
        return ("-" if is_negative else "") + binary
    
    def decimal_to_hex(self, n):
        if n == 0:
            return "0"
        hex_digits = "0123456789ABCDEF"
        is_negative = n < 0
        n = abs(n)
        hex_string = ""
        while n > 0:
            hex_string = hex_digits[n % 16] + hex_string
            n //= 16
        return ("-" if is_negative else "") + hex_string
    
    def binary_to_decimal(self, binary):
        is_negative = binary.startswith('-')
        if is_negative:
            binary = binary[1:]
        decimal = 0
        for i, bit in enumerate(reversed(binary)):
            if bit == '1':
                decimal += 2 ** i
            elif bit != '0':
                raise ValueError("Invalid binary digit")
        return -decimal if is_negative else decimal
    
    def binary_to_hex(self, binary):
        decimal = self.binary_to_decimal(binary)
        return self.decimal_to_hex(decimal)
    
    def hex_to_decimal(self, hex_string):
        is_negative = hex_string.startswith('-')
        if is_negative:
            hex_string = hex_string[1:]
        hex_digits = "0123456789ABCDEF"
        decimal = 0
        for i, digit in enumerate(reversed(hex_string.upper())):
            if digit in hex_digits:
                decimal += hex_digits.index(digit) * (16 ** i)
            else:
                raise ValueError("Invalid hexadecimal digit")
        return -decimal if is_negative else decimal
    
    def hex_to_binary(self, hex_string):
        decimal = self.hex_to_decimal(hex_string)
        return self.decimal_to_binary(decimal)
    
    def run(self):
        print("=== Binary/Decimal/Hexadecimal Converter ===")
        
        while True:
            print("\n1. Decimal to Binary/Hex")
            print("2. Binary to Decimal/Hex")
            print("3. Hexadecimal to Decimal/Binary")
            print("4. Exit")
            
            choice = input("\nChoose an option: ").strip()
            
            try:
                if choice == '1':
                    num = int(input("Enter decimal number: "))
                    print(f"Binary: {self.decimal_to_binary(num)}")
                    print(f"Hexadecimal: {self.decimal_to_hex(num)}")
                elif choice == '2':
                    binary = input("Enter binary number: ").strip()
                    decimal = self.binary_to_decimal(binary)
                    print(f"Decimal: {decimal}")
                    print(f"Hexadecimal: {self.binary_to_hex(binary)}")
                elif choice == '3':
                    hex_num = input("Enter hexadecimal number: ").strip()
                    decimal = self.hex_to_decimal(hex_num)
                    print(f"Decimal: {decimal}")
                    print(f"Binary: {self.hex_to_binary(hex_num)}")
                elif choice == '4':
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice.")
            except ValueError as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    converter = BinaryConverter()
    converter.run()
