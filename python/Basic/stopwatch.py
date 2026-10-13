import time
import sys

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"

def main():
    print("=== Simple Stopwatch ===")
    print("Commands: s=start, p=pause, r=reset, l=lap, q=quit")
    
    running = False
    start_time = 0
    elapsed = 0
    laps = []
    
    while True:
        if running:
            current_time = time.time()
            display_time = elapsed + (current_time - start_time)
            sys.stdout.write(f"\rElapsed Time: {format_time(display_time)}")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"\rElapsed Time: {format_time(elapsed)} (Paused)")
            sys.stdout.flush()
        
        command = input("\nCommand: ").strip().lower()
        
        if command == 's' and not running:
            start_time = time.time()
            running = True
            print("Stopwatch started.")
        elif command == 'p' and running:
            elapsed += time.time() - start_time
            running = False
            print("Stopwatch paused.")
        elif command == 'r':
            elapsed = 0
            if running:
                start_time = time.time()
            laps = []
            print("Stopwatch reset.")
        elif command == 'l' and running:
            lap_time = elapsed + (time.time() - start_time)
            laps.append(lap_time)
            print(f"Lap {len(laps)}: {format_time(lap_time)}")
        elif command == 'l' and not running:
            print("Start the stopwatch first to record laps.")
        elif command == 'q':
            if running:
                elapsed += time.time() - start_time
            print(f"\nFinal Time: {format_time(elapsed)}")
            if laps:
                print("\nLap Times:")
                for i, lap in enumerate(laps, 1):
                    print(f"  Lap {i}: {format_time(lap)}")
                
                save = input("Save laps to file? (y/n): ").lower()
                if save == 'y':
                    with open("stopwatch_laps.txt", "w") as f:
                        f.write(f"Final Time: {format_time(elapsed)}\n")
                        f.write("Lap Times:\n")
                        for i, lap in enumerate(laps, 1):
                            f.write(f"Lap {i}: {format_time(lap)}\n")
                    print("Laps saved to stopwatch_laps.txt")
            print("Goodbye!")
            break
        else:
            print("Invalid command. Use s, p, r, l, or q.")

if __name__ == "__main__":
    main()
