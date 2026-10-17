    
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# 1. Configure the pipeline options to disable OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False

# 2. Correctly map the pipeline options to the PDF format
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

source = "/Users/prudvinew/Documents/workspace/Newspaper-Pdf-extractor/src/InitialPhase-Extractor/ET Wealth 13- 19 July 2026.pdf"  # a document via a local path or URL

# 3. Convert your digital newspaper
result = converter.convert(source)

# 4. Save clean Markdown output
with open("newspaper_output.md", "w", encoding="utf-8") as f:
    f.write(result.document.export_to_markdown())
