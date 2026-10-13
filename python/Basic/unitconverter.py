class UnitConverter:
    def __init__(self):
        self.length_units = {
            'meters': 1, 'kilometers': 1000, 'centimeters': 0.01,
            'millimeters': 0.001, 'miles': 1609.344, 'feet': 0.3048,
            'inches': 0.0254, 'yards': 0.9144
        }
        self.weight_units = {
            'kilograms': 1, 'grams': 0.001, 'milligrams': 0.000001,
            'pounds': 0.453592, 'ounces': 0.0283495
        }
        self.volume_units = {
            'liters': 1, 'milliliters': 0.001, 'gallons': 3.78541,
            'cups': 0.236588, 'pints': 0.473176
        }
    
    def convert_length(self, value, from_unit, to_unit):
        meters = value * self.length_units[from_unit.lower()]
        return meters / self.length_units[to_unit.lower()]
    
    def convert_weight(self, value, from_unit, to_unit):
        kg = value * self.weight_units[from_unit.lower()]
        return kg / self.weight_units[to_unit.lower()]
    
    def convert_volume(self, value, from_unit, to_unit):
        liters = value * self.volume_units[from_unit.lower()]
        return liters / self.volume_units[to_unit.lower()]
    
    def convert_temperature(self, value, from_unit, to_unit):
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        if from_unit == 'celsius':
            celsius = value
        elif from_unit == 'fahrenheit':
            celsius = (value - 32) * 5/9
        elif from_unit == 'kelvin':
            celsius = value - 273.15
        else:
            raise ValueError("Invalid temperature unit")
        
        if to_unit == 'celsius':
            return celsius
        elif to_unit == 'fahrenheit':
            return celsius * 9/5 + 32
        elif to_unit == 'kelvin':
            return celsius + 273.15
    
    def run(self):
        converter = UnitConverter()
        
        while True:
            print("\n=== Unit Converter ===")
            print("1. Length")
            print("2. Weight")
            print("3. Volume")
            print("4. Temperature")
            print("5. Exit")
            
            choice = input("Choose a conversion category: ")
            
            if choice == '5':
                print("Goodbye!")
                break
            
            categories = {
                '1': ('length', converter.convert_length, converter.length_units),
                '2': ('weight', converter.convert_weight, converter.weight_units),
                '3': ('volume', converter.convert_volume, converter.volume_units),
                '4': ('temperature', 'temperature', None)
            }
            
            if choice not in categories:
                print("Invalid choice!")
                continue
            
            category_name = categories[choice][0]
            
            if choice == '4':  # Temperature
                from_unit = input("From (Celsius/Fahrenheit/Kelvin): ").lower()
                to_unit = input("To (Celsius/Fahrenheit/Kelvin): ").lower()
                value = float(input(f"Enter value in {from_unit}: "))
                result = converter.convert_temperature(value, from_unit, to_unit)
                print(f"{value} {from_unit} = {result:.2f} {to_unit}")
            else:
                convert_func = categories[choice][1]
                units = categories[choice][2]
                from_unit = input(f"From ({'/'.join(units.keys())}): ")
                to_unit = input(f"To ({'/'.join(units.keys())}): ")
                value = float(input(f"Enter value in {from_unit}: "))
                result = convert_func(value, from_unit, to_unit)
                print(f"{value} {from_unit} = {result:.4f} {to_unit}")

if __name__ == "__main__":
    converter = UnitConverter()
    converter.run()
