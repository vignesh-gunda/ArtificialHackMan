import os
import asyncio
from typing import Dict, Any
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

class DeepSeekOCRService:
    def __init__(self, api_token: str = None):
        """
        Open-source OCR service using Tesseract OCR
        No API tokens required - fully local processing
        """
        self.provider = "tesseract"
        
        # Configure Tesseract (you may need to adjust the path based on your system)
        # On macOS with Homebrew: brew install tesseract
        # On Ubuntu: sudo apt-get install tesseract-ocr
        try:
            # Test if tesseract is available
            pytesseract.get_tesseract_version()
            print(f"Using Tesseract OCR version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            print(f"Warning: Tesseract not found. Please install it: {e}")
            print("macOS: brew install tesseract")
            print("Ubuntu: sudo apt-get install tesseract-ocr")
        
        # Configure OCR settings for better accuracy
        self.ocr_config = '--oem 3 --psm 6'

    def _clean_text(self, text: str) -> str:
        """Clean and format OCR text output"""
        if not text:
            return ""
        
        # Remove excessive whitespace using simple string operations
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove extra spaces
            cleaned_line = ' '.join(line.split())
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        # Join lines and remove excessive line breaks
        text = '\n'.join(cleaned_lines)
        
        # Fix common OCR errors
        text = text.replace('|', 'I')  # Common OCR mistake
        
        return text.strip()

    def _format_as_markdown(self, text: str, page_num: int) -> str:
        """Convert plain text to basic markdown format"""
        if not text:
            return ""
        
        lines = text.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append('')
                continue
            
            # Detect potential headers (lines that are all caps)
            if len(line) > 3 and line.isupper():
                markdown_lines.append(f"## {line}")
            # Detect bullet points
            elif line.startswith(('•', '-', '*', '◦')):
                markdown_lines.append(f"- {line[1:].strip()}")
            # Detect numbered lists (simple approach)
            elif line and line[0].isdigit() and ('.' in line[:5] or ')' in line[:5]):
                markdown_lines.append(f"1. {line}")
            else:
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)

    async def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF through Tesseract OCR (page by page)"""
        doc = None
        try:
            # Validate file
            path = Path(pdf_path)
            if not path.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
            # Check for empty file
            if path.stat().st_size == 0:
                raise ValueError(f"PDF file is empty: {pdf_path}")

            doc = fitz.open(pdf_path)
            page_count = len(doc)
            full_markdown = ""
            
            print(f"Processing {page_count} pages with Tesseract OCR...")
            
            for page_num in range(page_count):
                try:
                    page = doc.load_page(page_num)
                    
                    # Convert page to high-resolution image for better OCR
                    mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for better OCR accuracy
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Enhance image for better OCR
                    # Convert to grayscale for better text recognition
                    if image.mode != 'L':
                        image = image.convert('L')
                    
                    # Run OCR with custom configuration
                    page_text = pytesseract.image_to_string(
                        image, 
                        config=self.ocr_config,
                        lang='eng'  # You can add more languages: 'eng+fra+deu'
                    )
                    
                    # Clean and format the text
                    cleaned_text = self._clean_text(page_text)
                    markdown_text = self._format_as_markdown(cleaned_text, page_num + 1)
                    
                    if markdown_text.strip():
                        full_markdown += f"\n\n--- Page {page_num + 1} ---\n\n{markdown_text}"
                    else:
                        full_markdown += f"\n\n--- Page {page_num + 1} ---\n\n*[No text detected on this page]*"
                    
                    print(f"Processed page {page_num + 1}/{page_count}")
                    
                except Exception as e:
                    print(f"Error processing page {page_num + 1}: {e}")
                    full_markdown += f"\n\n--- Page {page_num + 1} ---\n\n*[Error processing this page: {str(e)}]*"
            
            return {
                "markdown": full_markdown.strip(),
                "page_count": page_count,
                "detected_tables": [],  # Could be enhanced with table detection
                "status": "success",
                "provider": "tesseract",
                "attempt": 1 
            }
                
        except Exception as e:
            return {
                "markdown": "",
                "error": str(e),
                "status": "failed",
                "provider": "tesseract",
                "attempt": 1
            }
        finally:
            # Always close the document if it was opened
            if doc is not None:
                try:
                    doc.close()
                except:
                    pass  # Ignore errors when closing