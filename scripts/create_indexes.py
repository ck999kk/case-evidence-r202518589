import os
import re
import json
import hashlib
import urllib.parse
import subprocess
import csv
import sys
from pathlib import Path

def sha256_file(path):
    """Calculate SHA-256 hash of a file"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def get_pdf_pages(pdf_path):
    """Get page count from PDF using pdfinfo"""
    try:
        result = subprocess.run(
            ["pdfinfo", pdf_path], 
            capture_output=True, text=True, 
            stderr=subprocess.DEVNULL
        )
        match = re.search(r'Pages:\s+(\d+)', result.stdout)
        return int(match.group(1)) if match else 0
    except Exception:
        return 0

def get_git_remote():
    """Get GitHub owner/repo from git remote"""
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True, text=True
        )
        remote = result.stdout.strip()
        match = re.search(r'github\.com[:/](.+?)/(.+?)(?:\.git)?$', remote)
        if match:
            return match.group(1), match.group(2)
    except Exception:
        pass
    return "ck999kk", "case-evidence-r202518589"

def main():
    root = Path.cwd()
    der = root / "derived" / "pdf"
    ocr = root / "derived" / "ocr"
    docs = root / "docs"
    pub = docs / "p"
    idx = root / "indexes"
    
    # Create directories
    pub.mkdir(parents=True, exist_ok=True)
    idx.mkdir(parents=True, exist_ok=True)
    
    # Get GitHub info
    owner, repo = get_git_remote()
    
    master_list = []
    pages_list = []
    checksums = [["file", "sha256"]]
    
    print(f"Processing PDFs from {der}")
    
    # Process each PDF in derived/pdf/
    for pdf_file in sorted(der.glob("*.pdf")):
        print(f"Processing {pdf_file.name}...")
        
        # Calculate hash
        digest = sha256_file(pdf_file)
        short = digest[:40]
        
        # Public copy path
        pub_file = pub / f"{short}.pdf"
        
        # Copy only if content changed
        if not pub_file.exists() or sha256_file(pub_file) != digest:
            import shutil
            shutil.copy2(pdf_file, pub_file)
            print(f"  Copied to {pub_file.name}")
        
        # Get page count
        pages = get_pdf_pages(pdf_file)
        
        # Generate URLs
        base = f"https://{owner}.github.io/{repo}"
        pdf_url = f"{base}/p/{short}.pdf"
        viewer_url = f"{base}/web/viewer.html?file={urllib.parse.quote(pdf_url, safe='')}"
        
        # Document metadata
        doc_id = pdf_file.stem
        doc_meta = {
            "doc_id": doc_id,
            "source_file": f"evidence/{doc_id}.pdf",
            "derived_pdf": f"derived/pdf/{doc_id}.pdf",
            "published_pdf": f"docs/p/{short}.pdf",
            "sha256": digest,
            "page_count": pages,
            "viewer_url": viewer_url,
            "raw_url": pdf_url
        }
        master_list.append(doc_meta)
        
        # Page index entries
        ocr_dir = ocr / doc_id
        if ocr_dir.exists():
            for p in range(1, pages + 1):
                p_str = f"{p:04d}"
                pages_list.append({
                    "doc_id": doc_id,
                    "page": p,
                    "hocr": f"derived/ocr/{doc_id}/page-{p_str}.hocr",
                    "tsv": f"derived/ocr/{doc_id}/page-{p_str}.tsv"
                })
        
        # Checksum entry
        checksums.append([f"docs/p/{short}.pdf", digest])
    
    # Write indexes
    with open(idx / "master-index.jsonl", "w", encoding="utf-8") as f:
        for row in master_list:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    
    with open(idx / "page-index.jsonl", "w", encoding="utf-8") as f:
        for row in pages_list:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    
    with open(idx / "checksums.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(checksums)
    
    # Update docs/index.html with table
    rows = []
    for doc in master_list:
        rows.append(
            f"<tr>"
            f"<td>{doc['doc_id']}</td>"
            f"<td>{doc['page_count']}</td>"
            f"<td><a href='{doc['viewer_url']}' target='_blank'>View</a></td>"
            f"<td><a href='{doc['raw_url']}' target='_blank'>Download</a></td>"
            f"<td><code>{doc['sha256'][:12]}…</code></td>"
            f"</tr>"
        )
    
    table_html = (
        "<table><thead><tr>"
        "<th>Document ID</th><th>Pages</th><th>Viewer</th><th>Download</th><th>SHA256</th>"
        "</tr></thead><tbody>"
        + ("\n".join(rows) if rows else "<tr><td colspan='5'>No documents yet.</td></tr>")
        + "</tbody></table>"
    )
    
    # Update index.html
    index_file = docs / "index.html"
    if index_file.exists():
        html = index_file.read_text(encoding="utf-8")
        html = re.sub(
            r'<div id="index">.*?</div>', 
            f'<div id="index">{table_html}</div>', 
            html, 
            flags=re.DOTALL
        )
        index_file.write_text(html, encoding="utf-8")
    
    print(f"✅ Processed {len(master_list)} documents")
    print(f"✅ Generated {len(pages_list)} page index entries")
    print(f"✅ Updated docs/index.html")

if __name__ == "__main__":
    main()
