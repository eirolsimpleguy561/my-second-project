def celsius_to_fahrenheit(c):
    return (c * 9/5) + 32

def celsius_to_kelvin(c):
    return c + 273.15

def fahrenheit_to_celsius(f):
    return (f - 32) * 5/9

def kelvin_to_celsius(k):
    return k - 273.15


def convert_temperature(value, unit):
    unit = unit.upper()
    if unit == 'C':
        c = value
        f = celsius_to_fahrenheit(c)
        k = celsius_to_kelvin(c)
    elif unit == 'F':
        c = fahrenheit_to_celsius(value)
        f = value
        k = celsius_to_kelvin(c)
    elif unit == 'K':
        if value < 0:
            print("Kelvin cannot be negative.")
            return
        c = kelvin_to_celsius(value)
        f = celsius_to_fahrenheit(c)
        k = value
    else:
        print("Invalid unit. Use C, F, or K.")
        return

    print(f"\nCelsius:    {c:.2f} C")
    print(f"Fahrenheit: {f:.2f} F")
    print(f"Kelvin:     {k:.2f} K\n")


def main():
    print("=== Temperature Converter ===")
    while True:
        unit = input("Enter source unit (C / F / K) or 'exit': ").strip()
        if unit.lower() == 'exit':
            break
        try:
            value = float(input("Enter temperature value: "))
        except ValueError:
            print("Invalid number.")
            continue
        convert_temperature(value, unit)


if __name__ == "__main__":
    main()
