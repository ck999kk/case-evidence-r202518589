#!/bin/bash

# OCR Processing Runner Script
# ===========================
# This script runs the comprehensive OCR processor on the attachment directory

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
INPUT_DIR="$SCRIPT_DIR"

# Color output functions
print_header() {
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

print_info() {
    echo "[INFO] $1"
}

print_success() {
    echo "[SUCCESS] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

# Main execution
main() {
    print_header "COMPREHENSIVE OCR PROCESSING SYSTEM"
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not available"
        exit 1
    fi
    
    # Check if tesseract is available
    if ! command -v tesseract &> /dev/null; then
        print_error "Tesseract OCR is not available"
        print_info "Install with: brew install tesseract"
        exit 1
    fi
    
    print_info "Input directory: $INPUT_DIR"
    print_info "Python version: $(python3 --version)"
    print_info "Tesseract version: $(tesseract --version | head -1)"
    
    # Count files
    PDF_COUNT=$(fd "\.pdf$" "$INPUT_DIR" | wc -l | tr -d ' ')
    IMAGE_COUNT=$(fd "\.(png|jpg|jpeg|tiff|bmp|gif)$" "$INPUT_DIR" | wc -l | tr -d ' ')
    TOTAL_COUNT=$((PDF_COUNT + IMAGE_COUNT))
    
    print_info "Files to process:"
    print_info "  - PDF files: $PDF_COUNT"
    print_info "  - Image files: $IMAGE_COUNT"
    print_info "  - Total files: $TOTAL_COUNT"
    
    if [ "$TOTAL_COUNT" -eq 0 ]; then
        print_error "No files found to process"
        exit 1
    fi
    
    # Ask for confirmation
    echo ""
    echo "This will process $TOTAL_COUNT files using OCR technology."
    echo "Processing may take several minutes depending on file sizes."
    echo ""
    read -p "Do you want to continue? [y/N]: " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Processing cancelled by user"
        exit 0
    fi
    
    # Run the OCR processor
    print_header "STARTING OCR PROCESSING"
    
    if python3 "$SCRIPT_DIR/comprehensive_ocr_processor.py" "$INPUT_DIR" --workers 6; then
        print_success "OCR processing completed successfully!"
        
        # Show output directory
        OUTPUT_DIR="$INPUT_DIR/OCR_RESULTS"
        print_info "Results saved to: $OUTPUT_DIR"
        
        # List output files
        if [ -d "$OUTPUT_DIR" ]; then
            print_info "Generated files:"
            ls -la "$OUTPUT_DIR" | grep -v "^d" | awk '{print "  - " $9 " (" $5 " bytes)"}'
        fi
        
    else
        print_error "OCR processing failed!"
        exit 1
    fi
}

# Test mode function
test_run() {
    print_header "TEST MODE - PROCESSING SAMPLE FILES"
    
    if python3 "$SCRIPT_DIR/comprehensive_ocr_processor.py" "$INPUT_DIR" --test-run --workers 2; then
        print_success "Test run completed successfully!"
    else
        print_error "Test run failed!"
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
OCR Processing Runner Script

Usage: $0 [OPTION]

Options:
    (no option)    Run full OCR processing on all files
    test           Run test mode (process sample files only)
    help           Show this help message

Examples:
    $0             # Process all files
    $0 test        # Test mode
    $0 help        # Show help

This script will process all PDF and image files in the current directory
using advanced OCR technology and generate comprehensive reports.

EOF
}

# Handle command line arguments
case "${1:-}" in
    "test")
        test_run
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        print_info "Use '$0 help' for usage information"
        exit 1
        ;;
esac