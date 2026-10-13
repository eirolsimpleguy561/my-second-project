class MorseTranslator:
    def __init__(self):
        self.morse_dict = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
            '3': '...--', '4': '....-', '5': '.....', '6': '-....',
            '7': '--...', '8': '---..', '9': '----.', '.': '.-.-.-',
            ',': '--..--', '?': '..--..', '!': '-.-.--', ' ': '/'
        }
        self.reverse_dict = {v: k for k, v in self.morse_dict.items()}
    
    def text_to_morse(self, text):
        text = text.upper()
        morse_words = []
        for word in text.split(' '):
            morse_chars = []
            for char in word:
                if char in self.morse_dict:
                    morse_chars.append(self.morse_dict[char])
                else:
                    morse_chars.append('?')
            morse_words.append(' '.join(morse_chars))
        return ' / '.join(morse_words)
    
    def morse_to_text(self, morse):
        words = morse.split(' / ')
        text_words = []
        for word in words:
            chars = word.split()
            text_chars = []
            for code in chars:
                if code in self.reverse_dict:
                    text_chars.append(self.reverse_dict[code])
                else:
                    text_chars.append('?')
            text_words.append(''.join(text_chars))
        return ' '.join(text_words).capitalize()
    
    def play_morse_sound(self, morse_code):
        import time
        import winsound
        try:
            for char in morse_code:
                if char == '.':
                    winsound.Beep(800, 200)
                elif char == '-':
                    winsound.Beep(800, 600)
                elif char == ' ':
                    time.sleep(0.2)
                elif char == '/':
                    time.sleep(0.4)
                time.sleep(0.1)
        except:
            print("Sound playback not supported on this system.")
    
    def run(self):
        print("=== Morse Code Translator ===")
        print("1. Text to Morse Code")
        print("2. Morse Code to Text")
        print("3. Exit")
        
        while True:
            choice = input("\nChoose an option: ").strip()
            
            if choice == '1':
                text = input("Enter text to translate: ").strip()
                if text:
                    morse = self.text_to_morse(text)
                    print(f"\nMorse Code:\n{morse}")
                    sound = input("Play Morse code sound? (y/n): ").lower()
                    if sound == 'y':
                        self.play_morse_sound(morse)
            elif choice == '2':
                morse = input("Enter Morse code (use space between letters, / between words): ").strip()
                if morse:
                    text = self.morse_to_text(morse)
                    print(f"\nTranslated Text:\n{text}")
            elif choice == '3':
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    translator = MorseTranslator()
    translator.run()
