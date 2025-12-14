import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from services.ocr_service import DeepSeekOCRService
from agents.extraction_agent import build_extraction_graph, AgentState
from typing import List
from config.models import ExtractionResult

load_dotenv()

async def process_audit_folder():
    """Main orchestration function"""
    
    # Configuration
    input_folder = Path(os.getenv("INPUT_FOLDER", "inputs/Audit_Work_PDFs"))
    output_folder = Path(os.getenv("OUTPUT_FOLDER", "outputs/extracted_findings"))
    
    # Validate setup
    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")
    
    # Initialize services
    ocr_service = DeepSeekOCRService()
    agent = build_extraction_graph()
    
    # Process PDFs
    pdf_files = list(input_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {input_folder}")
        return
    
    print(f"🚀 Processing {len(pdf_files)} audit reports...")
    results = []
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_path.name}")
        
        # OCR Phase
        ocr_result = await ocr_service.process_pdf(str(pdf_path))
        if ocr_result["status"] == "failed":
            print(f"  ❌ OCR failed: {ocr_result['error']}")
            continue
        
        # Extraction Phase
        initial_state: AgentState = {
            "pdf_path": str(pdf_path),
            "markdown_content": ocr_result["markdown"],
            "extraction_result": None,
            "validation_errors": [],
            "retry_count": 0,
            "needs_retry": False
        }
        
        try:
            final_state = await agent.ainvoke(initial_state)
            result = final_state["extraction_result"]
            results.append(result)
            
            # Status reporting
            status = "✅" if not result.requires_human_review else "⚠️"
            print(f"  {status} {len(result.findings)} findings")
            
        except Exception as e:
            print(f"  ❌ Extraction failed: {e}")
        
        # Rate limiting
        # Rate limiting
        await asyncio.sleep(15.0)
    
    # Generate summary
    _generate_summary_report(results)
    return results

def _generate_summary_report(results: List[ExtractionResult]):
    """Create executive summary"""
    print("\n" + "="*60)
    print("📊 AUDIT EXTRACTION SUMMARY")
    print("="*60)
    
    if not results:
        print("No successful extractions.")
        return
    
    total_files = len(results)
    total_findings = sum(r.total_findings for r in results)
    needs_review = sum(1 for r in results if r.requires_human_review)
    critical_findings = sum(
        1 for r in results 
        for f in r.findings 
        if f.severity == "Critical"
    )
    
    print(f"Files processed:         {total_files}")
    print(f"Total findings:          {total_findings}")
    print(f"Critical findings:       {critical_findings}")
    print(f"Needing human review:    {needs_review}")
    print(f"Success rate:            {(total_files - needs_review) / total_files * 100:.1f}%")
    print(f"Output folder:           {Path('outputs/extracted_findings').absolute()}")
    print("="*60)

def main():
    """Entry point"""
    try:
        asyncio.run(process_audit_folder())
    except KeyboardInterrupt:
        print("\n\n🛑 Process interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()