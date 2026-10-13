from PIL import Image, ImageFilter, ImageEnhance
import os
import sys

class ImageConverter:
    def __init__(self, input_path, output_dir=None):
        self.input_path = input_path
        self.output_dir = output_dir or os.path.dirname(input_path)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def convert_format(self, output_format, quality=95):
        output_format = output_format.lower().replace('.', '')
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        output_path = os.path.join(self.output_dir, f"{base_name}.{output_format}")
        
        with Image.open(self.input_path) as img:
            if output_format in ['jpg', 'jpeg']:
                img = img.convert('RGB')
                img.save(output_path, output_format.upper(), quality=quality)
            else:
                img.save(output_path, output_format.upper())
        print(f"Converted to {output_format}: {output_path}")
        return output_path
    
    def resize(self, width=None, height=None, scale=1.0):
        with Image.open(self.input_path) as img:
            if scale != 1.0:
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
            else:
                new_width = width or img.width
                new_height = height or img.height
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            output_path = os.path.join(self.output_dir, f"resized_{os.path.basename(self.input_path)}")
            resized.save(output_path)
            print(f"Resized to {new_width}x{new_height}: {output_path}")
            return output_path
    
    def apply_filter(self, filter_type):
        filters = {
            'grayscale': lambda img: img.convert('L'),
            'sepia': self.sepia_filter,
            'blur': lambda img: img.filter(ImageFilter.BLUR),
            'sharpen': lambda img: img.filter(ImageFilter.SHARPEN),
            'edge': lambda img: img.filter(ImageFilter.FIND_EDGES),
            'contour': lambda img: img.filter(ImageFilter.CONTOUR)
        }
        
        if filter_type not in filters:
            print(f"Filter '{filter_type}' not available.")
            return None
        
        with Image.open(self.input_path) as img:
            filtered = filters[filter_type](img)
            output_path = os.path.join(self.output_dir, f"{filter_type}_{os.path.basename(self.input_path)}")
            
            if filter_type == 'grayscale':
                filtered.save(output_path)
            else:
                filtered.save(output_path)
            print(f"Applied {filter_type} filter: {output_path}")
            return output_path
    
    def sepia_filter(self, img):
        img = img.convert('RGB')
        width, height = img.size
        pixels = img.load()
        
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
        return img
    
    def rotate(self, angle):
        with Image.open(self.input_path) as img:
            rotated = img.rotate(angle, expand=True)
            output_path = os.path.join(self.output_dir, f"rotated_{os.path.basename(self.input_path)}")
            rotated.save(output_path)
            print(f"Rotated {angle} degrees: {output_path}")
            return output_path

def batch_process(directory, operation, **kwargs):
    extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    files = [f for f in os.listdir(directory) if os.path.splitext(f)[1].lower() in extensions]
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        converter = ImageConverter(filepath)
        
        if operation == 'convert':
            converter.convert_format(kwargs.get('format', 'jpg'))
        elif operation == 'resize':
            converter.resize(width=kwargs.get('width'), height=kwargs.get('height'), scale=kwargs.get('scale', 1.0))
        elif operation == 'filter':
            converter.apply_filter(kwargs.get('filter_type'))

def main():
    print("=== Image Converter Tool ===")
    
    while True:
        print("\n1. Convert format")
        print("2. Resize image")
        print("3. Apply filter")
        print("4. Rotate image")
        print("5. Batch process")
        print("6. Exit")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == '1':
            input_file = input("Input image path: ").strip()
            output_format = input("Output format (png/jpg/bmp/gif): ").strip()
            converter = ImageConverter(input_file)
            converter.convert_format(output_format)
        
        elif choice == '2':
            input_file = input("Input image path: ").strip()
            scale = input("Scale by percentage (enter number, e.g., 50 for half): ").strip()
            converter = ImageConverter(input_file)
            if scale:
                converter.resize(scale=float(scale) / 100)
            else:
                width = int(input("Width: "))
                height = int(input("Height: "))
                converter.resize(width=width, height=height)
        
        elif choice == '3':
            input_file = input("Input image path: ").strip()
            filter_type = input("Filter (grayscale/sepia/blur/sharpen/edge/contour): ").strip()
            converter = ImageConverter(input_file)
            converter.apply_filter(filter_type)
        
        elif choice == '4':
            input_file = input("Input image path: ").strip()
            angle = int(input("Rotation angle (0-360): ").strip())
            converter = ImageConverter(input_file)
            converter.rotate(angle)
        
        elif choice == '5':
            directory = input("Directory containing images: ").strip()
            print("Batch operations:")
            print("1. Convert all to JPG")
            print("2. Resize all to max width 800")
            print("3. Apply grayscale to all")
            batch_choice = input("Choose: ").strip()
            
            if batch_choice == '1':
                batch_process(directory, 'convert', format='jpg')
            elif batch_choice == '2':
                batch_process(directory, 'resize', width=800)
            elif batch_choice == '3':
                batch_process(directory, 'filter', filter_type='grayscale')
        
        elif choice == '6':
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()
