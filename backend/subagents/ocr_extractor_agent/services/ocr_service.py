import os
import base64
import asyncio
from typing import Dict, Any
from pathlib import Path
import fitz  # PyMuPDF
from openai import AsyncOpenAI
import httpx

class DeepSeekOCRService:
    def __init__(self, api_token: str = None):
        # Prioritize Replicate if token is explicitly set
        replicate_token = os.getenv("REPLICATE_API_TOKEN")
        friendli_token = os.getenv("FRIENDLI_TOKEN")
        
        self.api_token = api_token or replicate_token or friendli_token
        
        if not self.api_token:
            raise ValueError("FRIENDLI_TOKEN or REPLICATE_API_TOKEN not provided")
        
        # Determine provider - prioritize Replicate if token exists
        if replicate_token:
            self.provider = "replicate"
            self.httpx_client = httpx.AsyncClient(
                headers={"Authorization": f"Token {replicate_token}"},
                timeout=60.0
            )
            # Parse model version
            full_model_string = os.getenv("REPLICATE_MODEL", "lucataco/deepseek-ocr:cb3b474fbfc56b1664c8c7841550bccecbe7b74c30e45ce938ffca1180b4dff5")
            if ":" in full_model_string:
                self.model_version = full_model_string.split(":")[-1]
            else:
                self.model_version = full_model_string
        else:
            self.provider = "friendli"
        
        if self.provider == "friendli":
             base_url = "https://api.friendli.ai/serverless/v1"
             default_headers = {}
             team_id = os.getenv("FRIENDLI_TEAM_ID")
             if team_id:
                 default_headers["X-Friendli-Team"] = team_id

             self.client = AsyncOpenAI(
                 api_key=self.api_token,
                 base_url=base_url,
                 default_headers=default_headers
             )
             self.model_id = os.getenv("FRIENDLI_MODEL", "zai-org/GLM-4.6")
        
    async def _run_replicate(self, img_base64: str) -> str:
        url = "https://api.replicate.com/v1/predictions"
        payload = {
            "version": self.model_version,
            "input": {
                "image": f"data:image/png;base64,{img_base64}"
            }
        }
        
        resp = await self.httpx_client.post(url, json=payload)
        resp.raise_for_status()
        prediction = resp.json()
        prediction_id = prediction["id"]
        
        # Poll for completion
        while prediction["status"] not in ["succeeded", "failed", "canceled"]:
            await asyncio.sleep(1)
            resp = await self.httpx_client.get(f"{url}/{prediction_id}")
            resp.raise_for_status()
            prediction = resp.json()
            
        if prediction["status"] != "succeeded":
            raise RuntimeError(f"Replicate prediction failed: {prediction.get('error')}")
            
        output = prediction["output"]
        if isinstance(output, list):
            return "".join([str(x) for x in output])
        elif isinstance(output, dict):
            return output.get("markdown", "") or output.get("text", "")
        if output is None:
             return ""
        return str(output)

    async def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF through Friendli or Replicate OCR (page by page) with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        try:
            # Validate file
            path = Path(pdf_path)
            if not path.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
            # Check for empty file
            if path.stat().st_size == 0:
                 raise ValueError(f"PDF file is empty: {pdf_path}")

            doc = fitz.open(pdf_path)
            full_markdown = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better OCR
                img_data = pix.tobytes("png")
                img_base64 = base64.b64encode(img_data).decode()
                
                # Retry logic for each page
                page_success = False
                for attempt in range(max_retries):
                    try:
                        page_text = ""
                        if self.provider == "friendli":
                            response = await self.client.chat.completions.create(
                                model=self.model_id,
                                messages=[{
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "Transcribe the text in this image to Markdown. Preserve tables and formatting exactly."},
                                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                                    ]
                                }],
                                stream=False
                            )
                            page_text = response.choices[0].message.content
                        else:
                            # Replicate logic using httpx
                            page_text = await self._run_replicate(img_base64)

                        full_markdown += f"\n--- Page {page_num+1} ---\n{page_text}"
                        page_success = True
                        if self.provider == "replicate":
                             await asyncio.sleep(2) # moderate delay
                        break
                    except Exception as e:
                        print(f"    Page {page_num+1} attempt {attempt+1} failed ({self.provider}): {e}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            
                if not page_success:
                    return {
                        "markdown": full_markdown,
                        "error": f"Failed to process page {page_num+1} using {self.provider}",
                        "status": "failed",
                        "attempt": max_retries
                    }
            
            return {
                "markdown": full_markdown,
                "page_count": len(doc),
                "detected_tables": [],
                "status": "success",
                "attempt": 1 
            }
                
        except Exception as e:
            return {
                "markdown": "",
                "error": str(e),
                "status": "failed",
                "attempt": 1
            }