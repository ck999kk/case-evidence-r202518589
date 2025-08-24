import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def stem(filename):
    return Path(filename).stem

def process_pdf(src_path):
    """Process a single PDF with OCR"""
    print(f"Processing {src_path}...")
    
    basename = stem(src_path)
    out_path = f"derived/pdf/{basename}.pdf"
    ocr_dir = f"derived/ocr/{basename}"
    
    # Create OCR directory
    os.makedirs(ocr_dir, exist_ok=True)
    
    # Skip if already processed and output is newer
    if os.path.exists(out_path) and os.path.getmtime(out_path) > os.path.getmtime(src_path):
        print(f"  Skipping {basename} - already processed")
        return
    
    try:
        # OCRmyPDF to create searchable PDF + sidecar text
        cmd = [
            'ocrmypdf', 
            '--force-ocr', 
            '--output-type', 'pdf',
            '--optimize', '2',
            '--jobs', '2',  # Reduced for stability
            '--rotate-pages',
            '--skip-big', '50',
            '--sidecar', f"{ocr_dir}/sidecar.txt",
            '-l', 'eng',  # English only for now
            src_path,
            out_path
        ]
        
        print(f"  Running OCRmyPDF...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"  OCRmyPDF warning/error: {result.stderr}")
            # Continue anyway, OCRmyPDF often succeeds despite warnings
        
        # Per-page rasterization for hOCR/TSV
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"  Generating page images...")
            subprocess.run([
                'pdftoppm', '-r', '150', '-png', out_path, f"{tmpdir}/page"
            ], check=True)
            
            # Process each page image with Tesseract
            page_files = sorted([f for f in os.listdir(tmpdir) if f.startswith('page-') and f.endswith('.png')])
            for i, img_file in enumerate(page_files, 1):
                page_num = f"{i:04d}"
                img_path = os.path.join(tmpdir, img_file)
                
                print(f"  Processing page {i}...")
                
                # hOCR output
                subprocess.run([
                    'tesseract', img_path, 'stdout', '-l', 'eng', 'hocr'
                ], stdout=open(f"{ocr_dir}/page-{page_num}.hocr", 'w'), check=True)
                
                # TSV output
                subprocess.run([
                    'tesseract', img_path, 'stdout', '-l', 'eng', 'tsv'
                ], stdout=open(f"{ocr_dir}/page-{page_num}.tsv", 'w'), check=True)
        
        # Clean metadata
        print(f"  Cleaning metadata...")
        subprocess.run([
            'exiftool', '-Title=', '-Author=', '-Subject=', '-Creator=', '-Producer=', 
            '-overwrite_original', out_path
        ], capture_output=True)
        
        print(f"  ✅ Completed {basename}")
        
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout processing {basename}")
    except Exception as e:
        print(f"  ❌ Error processing {basename}: {e}")

def main():
    # Process all PDFs in evidence directory
    evidence_dir = Path("evidence")
    pdf_files = list(evidence_dir.glob("*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process first 5 PDFs as a test
    for pdf_file in pdf_files[:5]:
        process_pdf(str(pdf_file))

if __name__ == "__main__":
    main()
