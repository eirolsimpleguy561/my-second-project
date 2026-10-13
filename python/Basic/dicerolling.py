import random

def roll_dice(sides):
    return random.randint(1, sides)

def get_dice_face(value):
    faces = {
        1: "[   ]\n[ o ]\n[   ]",
        2: "[o  ]\n[   ]\n[  o]",
        3: "[o  ]\n[ o ]\n[  o]",
        4: "[o o]\n[   ]\n[o o]",
        5: "[o o]\n[ o ]\n[o o]",
        6: "[o o]\n[o o]\n[o o]"
    }
    return faces.get(value, f"Result: {value}")

def main():
    print("=== Dice Rolling Simulator ===")
    print("Available dice: 4, 6, 8, 10, 12, 20, 100 sides")
    
    while True:
        try:
            sides = int(input("\nNumber of sides on each die: "))
            if sides not in [4, 6, 8, 10, 12, 20, 100]:
                print("Please choose from available dice types.")
                continue
                
            num_dice = int(input("Number of dice to roll (1-10): "))
            if 1 <= num_dice <= 10:
                break
            print("Please enter a number between 1 and 10.")
        except ValueError:
            print("Invalid input. Please enter numbers.")
    
    results = [roll_dice(sides) for _ in range(num_dice)]
    total = sum(results)
    
    print("\n=== Results ===")
    for i, result in enumerate(results, 1):
        if sides == 6:
            print(f"Die {i}:\n{get_dice_face(result)}\n")
        else:
            print(f"Die {i}: {result}")
    
    print(f"Total sum: {total}")
    print(f"Average roll: {total/num_dice:.2f}")

if __name__ == "__main__":
    main()
