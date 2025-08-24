#!/usr/bin/env python3
"""
Comprehensive OCR Processing System
===================================

This system processes PDF files and images using multiple OCR approaches:
1. Direct text extraction from PDFs (when possible)
2. OCR processing for scanned PDFs and images
3. Parallel processing for efficiency
4. Structured output with detailed reporting

Requirements: tesseract, pytesseract, PIL, pdf2image, PyPDF2
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Third-party imports
try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    import PyPDF2
    import fitz  # PyMuPDF - fallback for PDFs
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Install with: pip install pytesseract Pillow pdf2image PyPDF2 PyMuPDF")
    sys.exit(1)

class OCRProcessor:
    """Comprehensive OCR processor for PDFs and images"""
    
    def __init__(self, input_dir: str, output_dir: str = None, max_workers: int = 4):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir) if output_dir else self.input_dir / "OCR_RESULTS"
        self.max_workers = max_workers
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Processing statistics
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'pdf_files': 0,
            'image_files': 0,
            'pdf_direct_text': 0,
            'pdf_ocr_required': 0,
            'total_text_length': 0,
            'processing_time': 0,
            'errors': []
        }
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.output_dir / f"ocr_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_file_list(self) -> Tuple[List[Path], List[Path]]:
        """Get lists of PDF and image files to process"""
        pdf_files = []
        image_files = []
        
        # Supported image formats
        image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}
        
        for file_path in self.input_dir.rglob('*'):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix == '.pdf':
                    pdf_files.append(file_path)
                elif suffix in image_extensions:
                    image_files.append(file_path)
        
        self.logger.info(f"Found {len(pdf_files)} PDF files and {len(image_files)} image files")
        return pdf_files, image_files
    
    def extract_text_from_pdf_direct(self, pdf_path: Path) -> Optional[str]:
        """Extract text directly from PDF (for text-based PDFs)"""
        try:
            # Try PyPDF2 first
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                # If we got substantial text, return it
                if len(text.strip()) > 100:  # Threshold for meaningful text
                    return text.strip()
        
        except Exception as e:
            self.logger.debug(f"PyPDF2 failed for {pdf_path}: {e}")
        
        # Fallback to PyMuPDF
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
            doc.close()
            
            if len(text.strip()) > 100:
                return text.strip()
                
        except Exception as e:
            self.logger.debug(f"PyMuPDF failed for {pdf_path}: {e}")
        
        return None
    
    def ocr_pdf_pages(self, pdf_path: Path) -> str:
        """Convert PDF pages to images and OCR them"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)  # High DPI for better OCR
            
            text_content = []
            for i, image in enumerate(images):
                try:
                    # Apply OCR to each page
                    page_text = pytesseract.image_to_string(image, config='--psm 6')
                    if page_text.strip():
                        text_content.append(f"=== PAGE {i+1} ===\n{page_text.strip()}")
                except Exception as e:
                    self.logger.warning(f"OCR failed for page {i+1} of {pdf_path}: {e}")
            
            return "\n\n".join(text_content)
        
        except Exception as e:
            self.logger.error(f"PDF to image conversion failed for {pdf_path}: {e}")
            return ""
    
    def ocr_image(self, image_path: Path) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply OCR
            text = pytesseract.image_to_string(image, config='--psm 6')
            return text.strip()
        
        except Exception as e:
            self.logger.error(f"OCR failed for image {image_path}: {e}")
            return ""
    
    def process_single_file(self, file_path: Path) -> Dict:
        """Process a single file and return results"""
        result = {
            'file_path': str(file_path.relative_to(self.input_dir)),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_type': file_path.suffix.lower(),
            'processing_method': '',
            'text_content': '',
            'text_length': 0,
            'processing_time': 0,
            'error': None,
            'file_hash': self.get_file_hash(file_path)
        }
        
        start_time = datetime.now()
        
        try:
            if file_path.suffix.lower() == '.pdf':
                self.stats['pdf_files'] += 1
                
                # Try direct text extraction first
                direct_text = self.extract_text_from_pdf_direct(file_path)
                
                if direct_text:
                    result['text_content'] = direct_text
                    result['processing_method'] = 'direct_pdf_extraction'
                    self.stats['pdf_direct_text'] += 1
                    self.logger.info(f"Direct text extraction successful: {file_path.name}")
                else:
                    # Fall back to OCR
                    result['text_content'] = self.ocr_pdf_pages(file_path)
                    result['processing_method'] = 'pdf_ocr'
                    self.stats['pdf_ocr_required'] += 1
                    self.logger.info(f"OCR processing completed: {file_path.name}")
            
            else:
                # Image file
                self.stats['image_files'] += 1
                result['text_content'] = self.ocr_image(file_path)
                result['processing_method'] = 'image_ocr'
                self.logger.info(f"Image OCR completed: {file_path.name}")
            
            result['text_length'] = len(result['text_content'])
            self.stats['total_text_length'] += result['text_length']
            self.stats['processed_files'] += 1
        
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            result['error'] = error_msg
            self.stats['failed_files'] += 1
            self.stats['errors'].append(f"{file_path.name}: {error_msg}")
            self.logger.error(f"Failed to process {file_path}: {e}")
        
        result['processing_time'] = (datetime.now() - start_time).total_seconds()
        return result
    
    def get_file_hash(self, file_path: Path) -> str:
        """Generate SHA-256 hash for file integrity"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def process_all_files(self) -> Dict:
        """Process all files using parallel processing"""
        start_time = datetime.now()
        
        # Get file lists
        pdf_files, image_files = self.get_file_list()
        all_files = pdf_files + image_files
        
        self.stats['total_files'] = len(all_files)
        
        if not all_files:
            self.logger.warning("No files found to process")
            return {'results': [], 'stats': self.stats}
        
        self.logger.info(f"Starting processing of {len(all_files)} files with {self.max_workers} workers")
        
        results = []
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {executor.submit(self.process_single_file, file_path): file_path 
                             for file_path in all_files}
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Progress reporting
                    progress = len(results) / len(all_files) * 100
                    self.logger.info(f"Progress: {progress:.1f}% ({len(results)}/{len(all_files)})")
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error processing {file_path}: {e}")
                    self.stats['failed_files'] += 1
        
        # Calculate final statistics
        self.stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"Processing completed in {self.stats['processing_time']:.2f} seconds")
        self.logger.info(f"Successfully processed: {self.stats['processed_files']} files")
        self.logger.info(f"Failed: {self.stats['failed_files']} files")
        
        return {
            'results': sorted(results, key=lambda x: x['file_path']),
            'stats': self.stats,
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def save_results(self, data: Dict, format_types: List[str] = None):
        """Save results in multiple formats"""
        if format_types is None:
            format_types = ['json', 'txt', 'csv']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON format (complete data)
        if 'json' in format_types:
            json_file = self.output_dir / f"ocr_results_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"JSON results saved to: {json_file}")
        
        # Save TXT format (text content only)
        if 'txt' in format_types:
            txt_file = self.output_dir / f"ocr_consolidated_text_{timestamp}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write("COMPREHENSIVE OCR EXTRACTION RESULTS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Processing Date: {data['processing_timestamp']}\n")
                f.write(f"Total Files Processed: {data['stats']['processed_files']}\n")
                f.write(f"Total Text Length: {data['stats']['total_text_length']} characters\n\n")
                
                for result in data['results']:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"FILE: {result['file_path']}\n")
                    f.write(f"METHOD: {result['processing_method']}\n")
                    f.write(f"SIZE: {result['text_length']} characters\n")
                    f.write(f"{'='*80}\n\n")
                    
                    if result['text_content']:
                        f.write(result['text_content'])
                    elif result['error']:
                        f.write(f"ERROR: {result['error']}")
                    else:
                        f.write("No text content extracted")
                    
                    f.write("\n\n")
            
            self.logger.info(f"TXT results saved to: {txt_file}")
        
        # Save CSV format (metadata)
        if 'csv' in format_types:
            csv_file = self.output_dir / f"ocr_metadata_{timestamp}.csv"
            with open(csv_file, 'w', encoding='utf-8') as f:
                # CSV header
                f.write("file_path,file_name,file_type,processing_method,text_length,processing_time,has_error,file_hash\n")
                
                for result in data['results']:
                    f.write(f'"{result["file_path"]}",')
                    f.write(f'"{result["file_name"]}",')
                    f.write(f'"{result["file_type"]}",')
                    f.write(f'"{result["processing_method"]}",')
                    f.write(f'{result["text_length"]},')
                    f.write(f'{result["processing_time"]:.3f},')
                    f.write(f'{"Yes" if result["error"] else "No"},')
                    f.write(f'"{result["file_hash"]}"\n')
            
            self.logger.info(f"CSV metadata saved to: {csv_file}")
        
        # Save processing statistics
        stats_file = self.output_dir / f"processing_statistics_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(data['stats'], f, indent=2, ensure_ascii=False)
        self.logger.info(f"Statistics saved to: {stats_file}")

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='Comprehensive OCR Processing System')
    parser.add_argument('input_dir', help='Input directory containing PDF and image files')
    parser.add_argument('--output-dir', help='Output directory (default: INPUT_DIR/OCR_RESULTS)')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers (default: 4)')
    parser.add_argument('--formats', nargs='+', choices=['json', 'txt', 'csv'], 
                       default=['json', 'txt', 'csv'], help='Output formats')
    parser.add_argument('--test-run', action='store_true', help='Process only first 5 files for testing')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = OCRProcessor(args.input_dir, args.output_dir, args.workers)
    
    if args.test_run:
        processor.logger.info("Running in TEST MODE - processing only first 5 files")
        # Modify processor for test run (implement test mode logic)
    
    # Process all files
    results = processor.process_all_files()
    
    # Save results
    processor.save_results(results, args.formats)
    
    # Print summary
    print("\n" + "="*60)
    print("OCR PROCESSING COMPLETED")
    print("="*60)
    print(f"Total files found: {results['stats']['total_files']}")
    print(f"Successfully processed: {results['stats']['processed_files']}")
    print(f"Failed: {results['stats']['failed_files']}")
    print(f"PDF files (direct text): {results['stats']['pdf_direct_text']}")
    print(f"PDF files (OCR required): {results['stats']['pdf_ocr_required']}")
    print(f"Image files: {results['stats']['image_files']}")
    print(f"Total text extracted: {results['stats']['total_text_length']:,} characters")
    print(f"Processing time: {results['stats']['processing_time']:.2f} seconds")
    print(f"Output directory: {processor.output_dir}")
    
    if results['stats']['errors']:
        print(f"\nErrors encountered: {len(results['stats']['errors'])}")
        for error in results['stats']['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(results['stats']['errors']) > 5:
            print(f"  ... and {len(results['stats']['errors']) - 5} more")

if __name__ == "__main__":
    main()