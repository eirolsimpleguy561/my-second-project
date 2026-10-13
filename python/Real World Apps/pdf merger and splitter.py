import PyPDF2
import os

def merge_pdfs(pdf_list, output_path):
    merger = PyPDF2.PdfMerger()
    for pdf in pdf_list:
        if os.path.exists(pdf):
            merger.append(pdf)
            print(f"Added: {pdf}")
        else:
            print(f"File not found: {pdf}")
    
    merger.write(output_path)
    merger.close()
    print(f"Merged PDF saved to: {output_path}")

def split_pdf(input_path, output_dir, pages=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(input_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)
        
        if pages is None:
            # Split every page individually
            for i in range(total_pages):
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[i])
                output_path = os.path.join(output_dir, f"page_{i+1}.pdf")
                with open(output_path, 'wb') as out_file:
                    writer.write(out_file)
                print(f"Saved: {output_path}")
        else:
            # Split specific page ranges
            writer = PyPDF2.PdfWriter()
            for page_num in pages:
                if 1 <= page_num <= total_pages:
                    writer.add_page(reader.pages[page_num - 1])
            output_path = os.path.join(output_dir, "extracted_pages.pdf")
            with open(output_path, 'wb') as out_file:
                writer.write(out_file)
            print(f"Extracted {len(pages)} pages to: {output_path}")

def extract_text(input_path):
    with open(input_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def rotate_pages(input_path, output_path, page_numbers, rotation):
    with open(input_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()
        
        for i, page in enumerate(reader.pages):
            if (i + 1) in page_numbers:
                page.rotate(rotation)
            writer.add_page(page)
        
        with open(output_path, 'wb') as out_file:
            writer.write(out_file)
        print(f"Rotated PDF saved to: {output_path}")

def main():
    print("=== PDF Merger and Splitter ===")
    print("1. Merge PDFs")
    print("2. Split PDF by pages")
    print("3. Extract text from PDF")
    print("4. Rotate PDF pages")
    
    choice = input("\nChoose an option: ").strip()
    
    if choice == '1':
        pdf_files = input("Enter PDF filenames separated by commas: ").strip().split(',')
        pdf_files = [f.strip() for f in pdf_files]
        output = input("Output filename: ").strip()
        if not output.endswith('.pdf'):
            output += '.pdf'
        merge_pdfs(pdf_files, output)
    
    elif choice == '2':
        input_file = input("Input PDF filename: ").strip()
        output_dir = input("Output directory: ").strip()
        split_type = input("1. Split all pages individually\n2. Extract specific pages\nChoice: ").strip()
        
        if split_type == '1':
            split_pdf(input_file, output_dir)
        elif split_type == '2':
            pages_input = input("Enter page numbers to extract (comma-separated): ").strip()
            pages = [int(p.strip()) for p in pages_input.split(',')]
            split_pdf(input_file, output_dir, pages)
    
    elif choice == '3':
        input_file = input("Input PDF filename: ").strip()
        text = extract_text(input_file)
        output_file = input("Save text to file (optional): ").strip()
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Text saved to {output_file}")
        else:
            print("\nExtracted Text:")
            print(text[:500] + "..." if len(text) > 500 else text)
    
    elif choice == '4':
        input_file = input("Input PDF filename: ").strip()
        output_file = input("Output filename: ").strip()
        pages_input = input("Page numbers to rotate (comma-separated): ").strip()
        pages = [int(p.strip()) for p in pages_input.split(',')]
        rotation = int(input("Rotation angle (90, 180, 270): ").strip())
        rotate_pages(input_file, output_file, pages, rotation)
    
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
