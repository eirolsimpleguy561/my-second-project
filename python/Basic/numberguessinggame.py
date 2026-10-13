import random


def play_game():
    secret = random.randint(1, 100)
    max_attempts = 7
    attempts = 0

    print("\n=== Number Guessing Game ===")
    print(f"Guess the number between 1 and 100. You have {max_attempts} attempts.\n")

    while attempts < max_attempts:
        try:
            guess = int(input(f"Attempt {attempts + 1}/{max_attempts} - Your guess: "))
        except ValueError:
            print("Please enter a valid number.")
            continue

        attempts += 1

        if guess < secret:
            print("Too low! Try higher.")
        elif guess > secret:
            print("Too high! Try lower.")
        else:
            print(f"Correct! You guessed it in {attempts} attempts!")
            return attempts

    print(f"Out of attempts! The number was {secret}.")
    return None


def main():
    best_score = None
    while True:
        result = play_game()
        if result and (best_score is None or result < best_score):
            best_score = result
            print(f"New best score: {best_score} attempts!")
        elif best_score:
            print(f"Best score so far: {best_score} attempts.")

        again = input("\nPlay again? (yes/no): ").strip().lower()
        if again != "yes":
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
