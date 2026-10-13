import random

def get_winner(player, computer):
    if player == computer:
        return "tie"
    
    winning_moves = {
        'rock': 'scissors',
        'paper': 'rock',
        'scissors': 'paper'
    }
    
    if winning_moves[player] == computer:
        return "player"
    else:
        return "computer"

def display_choice(choice):
    ascii_art = {
        'rock': """
    _______
---'   ____)
      (_____)
      (_____)
      (____)
---.__(___)
""",
        'paper': """
    _______
---'   ____)____
          ______)
          _______)
         _______)
---.__________)
""",
        'scissors': """
    _______
---'   ____)____
          ______)
       __________)
      (____)
---.__(___)
"""
    }
    return ascii_art.get(choice, choice)

def main():
    print("=== Rock Paper Scissors ===")
    print("Rules: Rock beats Scissors, Scissors beats Paper, Paper beats Rock")
    
    choices = ['rock', 'paper', 'scissors']
    
    while True:
        try:
            rounds_to_win = int(input("\nBest of how many? (3 or 5): "))
            if rounds_to_win in [3, 5]:
                rounds_needed = (rounds_to_win // 2) + 1
                break
            print("Please choose 3 or 5.")
        except ValueError:
            print("Invalid input. Please enter 3 or 5.")
    
    player_score = 0
    computer_score = 0
    round_num = 1
    
    while player_score < rounds_needed and computer_score < rounds_needed:
        print(f"\n--- Round {round_num} ---")
        print(f"Score: Player {player_score} - {computer_score} Computer")
        
        while True:
            player_choice = input("Choose rock, paper, or scissors: ").lower()
            if player_choice in choices:
                break
            print("Invalid choice! Please choose rock, paper, or scissors.")
        
        computer_choice = random.choice(choices)
        
        print(f"\nPlayer chose:\n{display_choice(player_choice)}")
        print(f"Computer chose:\n{display_choice(computer_choice)}")
        
        winner = get_winner(player_choice, computer_choice)
        
        if winner == "player":
            print("🎉 You win this round! 🎉")
            player_score += 1
        elif winner == "computer":
            print("🤖 Computer wins this round! 🤖")
            computer_score += 1
        else:
            print("It's a tie!")
        
        round_num += 1
    
    print(f"\n{'='*40}")
    if player_score > computer_score:
        print("🏆 Congratulations! You won the match! 🏆")
    else:
        print("💻 Computer wins the match! Better luck next time! 💻")
    print(f"Final Score: Player {player_score} - {computer_score} Computer")
    print(f"{'='*40}")
    
    play_again = input("\nWould you like to play again? (y/n): ").lower()
    if play_again == 'y':
        main()
    else:
        print("Thanks for playing!")

if __name__ == "__main__":
    main()
