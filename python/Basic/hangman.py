import random

def get_random_word():
    word_list = [
        'python', 'programming', 'computer', 'algorithm', 'developer',
        'hangman', 'challenge', 'learning', 'code', 'function',
        'variable', 'dictionary', 'loop', 'condition', 'debugging'
    ]
    return random.choice(word_list).lower()

def display_hangman(attempts):
    stages = [
        """
           --------
           |      |
           |      O
           |     \\|/
           |      |
           |     / \\
           -
        """,
        """
           --------
           |      |
           |      O
           |     \\|/
           |      |
           |     /
           -
        """,
        """
           --------
           |      |
           |      O
           |     \\|/
           |      |
           |
           -
        """,
        """
           --------
           |      |
           |      O
           |     \\|
           |      |
           |
           -
        """,
        """
           --------
           |      |
           |      O
           |      |
           |      |
           |
           -
        """,
        """
           --------
           |      |
           |      O
           |
           |
           |
           -
        """,
        """
           --------
           |      |
           |
           |
           |
           |
           -
        """
    ]
    return stages[attempts]

def display_word(word, guessed_letters):
    return ' '.join([letter if letter in guessed_letters else '_' for letter in word])

def main():
    print("=== Hangman Game ===")
    
    while True:
        word = get_random_word()
        word_letters = set(word)
        guessed_letters = set()
        incorrect_guesses = 0
        max_incorrect = 6
        
        while incorrect_guesses < max_incorrect and word_letters - guessed_letters:
            print("\n" + display_hangman(incorrect_guesses))
            print(f"Word: {display_word(word, guessed_letters)}")
            print(f"Guessed letters: {' '.join(sorted(guessed_letters)) if guessed_letters else 'None'}")
            print(f"Incorrect guesses: {incorrect_guesses}/{max_incorrect}")
            
            guess = input("Guess a letter: ").lower().strip()
            
            if len(guess) != 1 or not guess.isalpha():
                print("Please enter a single letter.")
                continue
            
            if guess in guessed_letters:
                print(f"You already guessed '{guess}'. Try a different letter.")
                continue
            
            guessed_letters.add(guess)
            
            if guess in word_letters:
                print(f"✓ Good guess! '{guess}' is in the word.")
            else:
                incorrect_guesses += 1
                print(f"✗ Sorry, '{guess}' is not in the word.")
        
        print("\n" + display_hangman(incorrect_guesses))
        
        if incorrect_guesses == max_incorrect:
            print(f"💀 You lost! The word was: {word} 💀")
        else:
            print(f"🎉 Congratulations! You guessed the word: {word} 🎉")
        
        play_again = input("\nWould you like to play again? (y/n): ").lower()
        if play_again != 'y':
            print("Thanks for playing Hangman!")
            break

if __name__ == "__main__":
    main()
