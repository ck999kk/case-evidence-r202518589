#!/usr/bin/env python3
"""
Build Search Index for Case Evidence R202518589
Generates JavaScript search index from OCR text data
"""

import os
import json
import re
from pathlib import Path

def clean_text(text):
    """Clean and normalize text for search indexing"""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    return text

def extract_document_info(filename):
    """Extract document type and metadata from filename"""
    filename_lower = filename.lower()
    
    # Document type classification
    if 'vcat' in filename_lower:
        doc_type = 'VCAT Legal Document'
        category = 'legal'
    elif 'receipt' in filename_lower:
        doc_type = 'Financial Receipt'
        category = 'financial'
    elif 'notice' in filename_lower:
        doc_type = 'Official Notice'
        category = 'notice'
    elif 'exhibit' in filename_lower:
        doc_type = 'Evidence Exhibit'
        category = 'evidence'
    elif 'application' in filename_lower:
        doc_type = 'Application Document'
        category = 'application'
    else:
        doc_type = 'Supporting Document'
        category = 'support'
    
    return doc_type, category

def build_search_index():
    """Build comprehensive search index from OCR data"""
    print("🔍 Building search index from OCR data...")
    
    base_dir = Path('/Users/chawakornkamnuansil/dev/case-evidence-r202518589')
    ocr_dir = base_dir / 'derived' / 'ocr'
    docs_dir = base_dir / 'docs'
    
    search_data = {
        'documents': [],
        'index': {},
        'categories': {},
        'stats': {
            'total_documents': 0,
            'total_words': 0,
            'categories': {}
        }
    }
    
    category_counts = {}
    total_words = 0
    
    # Process each OCR directory
    for ocr_folder in sorted(ocr_dir.iterdir()):
        if not ocr_folder.is_dir():
            continue
            
        doc_name = ocr_folder.name
        sidecar_file = ocr_folder / 'sidecar.txt'
        
        # Skip if no OCR text available
        if not sidecar_file.exists():
            continue
            
        # Read OCR text
        try:
            with open(sidecar_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
        except:
            continue
            
        # Clean text
        clean_content = clean_text(text_content)
        if len(clean_content) < 10:  # Skip nearly empty documents
            continue
            
        # Extract document metadata
        doc_type, category = extract_document_info(doc_name)
        
        # Find corresponding PDF hash
        master_index_file = docs_dir / 'master-index.jsonl'
        pdf_hash = None
        
        if master_index_file.exists():
            with open(master_index_file, 'r') as f:
                for line in f:
                    try:
                        doc_data = json.loads(line.strip())
                        if doc_data.get('original_filename') == f"{doc_name}.pdf":
                            pdf_hash = doc_data.get('sha256_hash')
                            break
                    except:
                        continue
        
        # Create document entry
        doc_entry = {
            'id': len(search_data['documents']),
            'title': doc_name,
            'type': doc_type,
            'category': category,
            'text': clean_content[:2000],  # Limit for performance
            'word_count': len(clean_content.split()),
            'hash': pdf_hash,
            'view_url': f"web/viewer.html?file=../p/{pdf_hash}.pdf" if pdf_hash else None,
            'download_url': f"p/{pdf_hash}.pdf" if pdf_hash else None
        }
        
        search_data['documents'].append(doc_entry)
        
        # Build word index
        words = re.findall(r'\b\w+\b', clean_content.lower())
        for word in words:
            if len(word) >= 3:  # Only index words 3+ characters
                if word not in search_data['index']:
                    search_data['index'][word] = []
                if doc_entry['id'] not in search_data['index'][word]:
                    search_data['index'][word].append(doc_entry['id'])
        
        # Update statistics
        category_counts[category] = category_counts.get(category, 0) + 1
        total_words += doc_entry['word_count']
        
        print(f"  📄 Indexed: {doc_name} ({doc_entry['word_count']} words)")
    
    # Finalize statistics
    search_data['stats']['total_documents'] = len(search_data['documents'])
    search_data['stats']['total_words'] = total_words
    search_data['stats']['categories'] = category_counts
    
    # Generate JavaScript search index
    js_content = f"""
// Case Evidence R202518589 - Search Index
// Generated automatically from OCR data
// Total: {len(search_data['documents'])} documents, {total_words:,} words

const SEARCH_DATA = {json.dumps(search_data, indent=2, ensure_ascii=False)};

// Search functionality
class EvidenceSearch {{
    constructor() {{
        this.data = SEARCH_DATA;
        this.results = [];
    }}
    
    search(query) {{
        if (!query || query.length < 2) {{
            return [];
        }}
        
        const searchTerms = query.toLowerCase().split(/\\s+/);
        const matchedDocs = new Map();
        
        // Search through word index
        searchTerms.forEach(term => {{
            Object.keys(this.data.index).forEach(word => {{
                if (word.includes(term)) {{
                    this.data.index[word].forEach(docId => {{
                        const score = matchedDocs.get(docId) || 0;
                        matchedDocs.set(docId, score + (word === term ? 2 : 1));
                    }});
                }}
            }});
        }});
        
        // Also search in document titles and text
        this.data.documents.forEach((doc, index) => {{
            const titleMatch = searchTerms.some(term => 
                doc.title.toLowerCase().includes(term)
            );
            const textMatch = searchTerms.some(term => 
                doc.text.toLowerCase().includes(term)
            );
            
            if (titleMatch || textMatch) {{
                const score = matchedDocs.get(index) || 0;
                matchedDocs.set(index, score + (titleMatch ? 3 : 1));
            }}
        }});
        
        // Sort by relevance score
        const results = Array.from(matchedDocs.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 20)  // Top 20 results
            .map(([docId, score]) => ({{
                ...this.data.documents[docId],
                relevanceScore: score
            }}));
            
        return results;
    }}
    
    getCategories() {{
        return this.data.stats.categories;
    }}
    
    filterByCategory(category) {{
        return this.data.documents.filter(doc => doc.category === category);
    }}
    
    getStats() {{
        return this.data.stats;
    }}
}}

// Global search instance
window.evidenceSearch = new EvidenceSearch();
"""
    
    # Write JavaScript search index
    search_js_file = docs_dir / 'search.js'
    with open(search_js_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"✅ Search index built successfully!")
    print(f"   📊 {len(search_data['documents'])} documents indexed")
    print(f"   📝 {total_words:,} total words")
    print(f"   🏷️  Categories: {', '.join(category_counts.keys())}")
    print(f"   💾 Saved to: {search_js_file}")
    
    return search_data

if __name__ == '__main__':
    build_search_index()