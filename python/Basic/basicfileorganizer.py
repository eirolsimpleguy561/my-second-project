import os
import shutil
import json

class FileOrganizer:
    def __init__(self, config_file="organizer_config.json"):
        self.config = self.load_config(config_file)
        self.moved_files = []
    
    def load_config(self, config_file):
        default_config = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
            "Videos": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"],
            "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Code": [".py", ".js", ".html", ".css", ".cpp", ".java", ".json"],
            "Executables": [".exe", ".msi", ".app", ".sh", ".bat"],
            "Others": []
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def get_category(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        for category, extensions in self.config.items():
            if ext in extensions:
                return category
        return "Others"
    
    def get_unique_filename(self, filepath):
        if not os.path.exists(filepath):
            return filepath
        
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        return f"{base}_{counter}{ext}"
    
    def organize(self, directory, dry_run=True):
        self.moved_files = []
        
        if not os.path.exists(directory):
            print(f"Directory '{directory}' does not exist.")
            return
        
        files = [f for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f))]
        
        if not files:
            print("No files to organize.")
            return
        
        print(f"\n{'PREVIEW' if dry_run else 'ORGANIZING'} files in: {directory}")
        print("-" * 50)
        
        for filename in files:
            category = self.get_category(filename)
            category_path = os.path.join(directory, category)
            
            if not dry_run:
                os.makedirs(category_path, exist_ok=True)
            
            src = os.path.join(directory, filename)
            dest = os.path.join(category_path, filename)
            
            if not dry_run:
                if os.path.exists(dest):
                    dest = self.get_unique_filename(dest)
                shutil.move(src, dest)
                self.moved_files.append((src, dest))
            
            print(f"{filename} -> {category}/")
        
        if dry_run:
            print("\nThis was a preview. Run with dry_run=False to actually move files.")
        else:
            print(f"\nMoved {len(self.moved_files)} files.")
    
    def undo(self):
        if not self.moved_files:
            print("No moves to undo.")
            return
        
        for src, dest in reversed(self.moved_files):
            if os.path.exists(dest):
                shutil.move(dest, src)
                print(f"Undid: {os.path.basename(dest)}")
        
        self.moved_files = []
        print("Undo complete.")

def main():
    organizer = FileOrganizer()
    
    while True:
        print("\n=== File Organizer ===")
        print("1. Preview organization")
        print("2. Organize files")
        print("3. Undo last organization")
        print("4. Exit")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == '1':
            directory = input("Enter directory path: ").strip()
            organizer.organize(directory, dry_run=True)
        elif choice == '2':
            directory = input("Enter directory path: ").strip()
            confirm = input("This will move files. Continue? (y/n): ").lower()
            if confirm == 'y':
                organizer.organize(directory, dry_run=False)
        elif choice == '3':
            organizer.undo()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
