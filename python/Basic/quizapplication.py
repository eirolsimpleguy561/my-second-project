import json

def load_quiz(filename="quiz.json"):
    default_quiz = {
        "title": "General Knowledge Quiz",
        "questions": [
            {
                "text": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct": 2,
                "explanation": "Paris is the capital and most populous city of France."
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "options": ["Mars", "Jupiter", "Venus", "Saturn"],
                "correct": 0,
                "explanation": "Mars is called the Red Planet because of its reddish appearance."
            },
            {
                "text": "What is 7 * 8?",
                "options": ["48", "56", "64", "72"],
                "correct": 1,
                "explanation": "7 multiplied by 8 equals 56."
            }
        ]
    }
    
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{filename} not found. Using default quiz.")
        return default_quiz

def run_quiz(quiz_data):
    print(f"\n=== {quiz_data['title']} ===")
    print(f"Total questions: {len(quiz_data['questions'])}")
    
    score = 0
    incorrect = []
    
    for i, q in enumerate(quiz_data['questions'], 1):
        print(f"\nQuestion {i}: {q['text']}")
        for j, opt in enumerate(q['options'], 1):
            print(f"  {j}. {opt}")
        
        while True:
            try:
                answer = int(input("Your answer (1-4): ")) - 1
                if 0 <= answer < 4:
                    break
                print("Please enter a number between 1 and 4.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        if answer == q['correct']:
            print("✓ Correct!")
            score += 1
        else:
            print(f"✗ Incorrect! The correct answer was: {q['options'][q['correct']]}")
            if 'explanation' in q:
                print(f"Explanation: {q['explanation']}")
            incorrect.append({
                'question': q['text'],
                'your_answer': q['options'][answer],
                'correct_answer': q['options'][q['correct']]
            })
    
    percentage = (score / len(quiz_data['questions'])) * 100
    print(f"\n{'='*50}")
    print(f"Quiz Complete!")
    print(f"Your Score: {score}/{len(quiz_data['questions'])}")
    print(f"Percentage: {percentage:.1f}%")
    
    if percentage >= 80:
        print("🎉 Excellent work! 🎉")
    elif percentage >= 60:
        print("👍 Good job! Keep practicing! 👍")
    else:
        print("📚 Keep studying! You'll do better next time! 📚")
    
    if incorrect:
        print("\nQuestions to review:")
        for i, item in enumerate(incorrect, 1):
            print(f"{i}. {item['question']}")
            print(f"   Your answer: {item['your_answer']}")
            print(f"   Correct answer: {item['correct_answer']}\n")

def main():
    quiz_data = load_quiz()
    run_quiz(quiz_data)
    
    play_again = input("\nWould you like to take another quiz? (y/n): ").lower()
    if play_again == 'y':
        main()
    else:
        print("Thanks for playing!")

if __name__ == "__main__":
    main()
