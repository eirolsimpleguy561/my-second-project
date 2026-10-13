import random

def get_story_template(story_number):
    stories = {
        1: "Today I went to the {place}. I saw a {adjective} {animal} {verb}ing in the {noun}. It was {adverb} {adjective}!",
        2: "My {adjective} friend {name} and I decided to {verb} to the {place}. We found a {color} {noun} that could {verb} {adverb}. We had an {adjective} adventure!",
        3: "Once upon a time, there was a {adjective} {noun} who loved to {verb} {adverb}. Every {day_of_week}, they would go to the {place} to eat {food} and {verb} with their {adjective} friends."
    }
    return stories.get(story_number, stories[1])

def get_user_inputs(word_types):
    user_words = {}
    for word_type in word_types:
        if word_type == 'name':
            user_words[word_type] = input(f"Enter a {word_type}: ").strip()
        elif word_type == 'day_of_week':
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            print(f"Available days: {', '.join(days)}")
            user_words[word_type] = input(f"Enter a {word_type}: ").strip().capitalize()
        elif word_type == 'color':
            user_words[word_type] = input(f"Enter a {word_type} (e.g., red, blue, green): ").strip()
        elif word_type == 'food':
            user_words[word_type] = input(f"Enter a type of {word_type}: ").strip()
        else:
            user_words[word_type] = input(f"Enter an {word_type}: ").strip() if word_type[0] in 'aeiou' else input(f"Enter a {word_type}: ").strip()
    return user_words

def main():
    print("=== Mad Libs Generator ===")
    print("\nAvailable stories:")
    print("1. Animal Adventure")
    print("2. Friendship Tale")
    print("3. Fantasy Story")
    
    try:
        story_choice = int(input("\nChoose a story (1-3): "))
    except ValueError:
        story_choice = 1
    
    template = get_story_template(story_choice)
    
    word_types = []
    start = 0
    while '{' in template[start:]:
        open_brace = template.find('{', start)
        close_brace = template.find('}', open_brace)
        word_type = template[open_brace+1:close_brace]
        if word_type not in word_types:
            word_types.append(word_type)
        start = close_brace + 1
    
    print(f"\nPlease provide the following words:")
    user_words = get_user_inputs(word_types)
    
    madlib = template.format(**user_words)
    
    print("\n" + "="*50)
    print("Your Mad Libs Story:")
    print("="*50)
    print(madlib)
    print("="*50)
    
    save_option = input("\nSave this story to a file? (y/n): ").lower()
    if save_option == 'y':
        filename = input("Enter filename (without extension): ").strip() or "madlib_story"
        with open(f"{filename}.txt", "w") as file:
            file.write(madlib)
        print(f"Story saved to {filename}.txt")
    
    print("\nThanks for playing Mad Libs!")

if __name__ == "__main__":
    main()
