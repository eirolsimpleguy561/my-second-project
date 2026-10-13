import os
from collections import Counter

STOP_WORDS = {"the", "a", "an", "is", "it", "in", "on", "at", "to", "and", "or", "of", "for", "with"}


def analyze_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    words = content.lower().split()
    chars = len(content)

    # Remove punctuation from words
    clean_words = [w.strip('.,!?;:"\'()[]') for w in words]
    filtered = [w for w in clean_words if w and w not in STOP_WORDS]

    word_freq = Counter(filtered)
    top_words = word_freq.most_common(10)

    print(f"\n--- Analysis of '{filepath}' ---")
    print(f"Lines      : {len(lines)}")
    print(f"Words      : {len(words)}")
    print(f"Characters : {chars}")
    print("\nTop 10 Most Frequent Words:")
    for word, count in top_words:
        print(f"  {word:<20} {count}")
    print()


def main():
    filepath = input("Enter the path to the text file: ").strip()
    analyze_file(filepath)


if __name__ == "__main__":
    main()
