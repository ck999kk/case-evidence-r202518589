import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import time

def process_pdf(src_path):
    """Process a single PDF with OCR"""
    basename = Path(src_path).stem
    out_path = f"derived/pdf/{basename}.pdf"
    ocr_dir = f"derived/ocr/{basename}"
    
    print(f"📄 Processing: {basename}")
    
    # Create OCR directory
    os.makedirs(ocr_dir, exist_ok=True)
    
    # Skip if already processed and output is newer
    if os.path.exists(out_path) and os.path.getmtime(out_path) > os.path.getmtime(src_path):
        print(f"  ⏭️  Already processed - skipping")
        return True
    
    try:
        # OCRmyPDF with reduced settings for stability
        cmd = [
            'ocrmypdf', 
            '--force-ocr', 
            '--output-type', 'pdf',
            '--optimize', '1',
            '--jobs', '1',  # Single thread for stability
            '--rotate-pages',
            '--skip-big', '100',
            '--sidecar', f"{ocr_dir}/sidecar.txt",
            '-l', 'eng',
            '--deskew',
            '--clean',
            src_path,
            out_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0 and not os.path.exists(out_path):
            print(f"  ❌ OCRmyPDF failed: {result.stderr[:100]}")
            return False
        
        # Generate page images and OCR data
        with tempfile.TemporaryDirectory() as tmpdir:
            # Lower resolution for faster processing
            subprocess.run([
                'pdftoppm', '-r', '150', '-png', out_path, f"{tmpdir}/page"
            ], check=True, timeout=120)
            
            # Process each page
            page_files = sorted([f for f in os.listdir(tmpdir) if f.startswith('page-') and f.endswith('.png')])
            for i, img_file in enumerate(page_files, 1):
                page_num = f"{i:04d}"
                img_path = os.path.join(tmpdir, img_file)
                
                # hOCR output
                with open(f"{ocr_dir}/page-{page_num}.hocr", 'w') as f:
                    subprocess.run([
                        'tesseract', img_path, 'stdout', '-l', 'eng', 'hocr'
                    ], stdout=f, timeout=60)
                
                # TSV output  
                with open(f"{ocr_dir}/page-{page_num}.tsv", 'w') as f:
                    subprocess.run([
                        'tesseract', img_path, 'stdout', '-l', 'eng', 'tsv'
                    ], stdout=f, timeout=60)
        
        # Clean metadata
        subprocess.run([
            'exiftool', '-Title=', '-Author=', '-Subject=', '-Creator=', '-Producer=', 
            '-overwrite_original', out_path
        ], capture_output=True, timeout=30)
        
        print(f"  ✅ Completed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    evidence_dir = Path("evidence")
    pdf_files = sorted(list(evidence_dir.glob("*.pdf")))
    
    print(f"🎯 Processing {len(pdf_files)} PDF files")
    
    successful = 0
    failed = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] ", end="")
        if process_pdf(str(pdf_file)):
            successful += 1
        else:
            failed += 1
        
        # Small delay to prevent system overload
        time.sleep(0.5)
    
    print(f"\n🏁 COMPLETE: {successful} successful, {failed} failed")
    return successful, failed

if __name__ == "__main__":
    main()
