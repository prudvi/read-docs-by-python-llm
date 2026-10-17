import json
import os
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# 1. Setup paths
pdf_path = "/Users/prudvinew/Documents/workspace/Newspaper-Pdf-extractor/src/InitialPhase-Extractor/TH BL HD Bangalore 21~07~2026.pdf"  # a document via a local path or URL
output_dir = Path("newspaper_extraction_output")
output_dir.mkdir(exist_ok=True)

# Create subdirectories for tidy organization
images_dir = output_dir / "images"
tables_dir = output_dir / "tables"
images_dir.mkdir(exist_ok=True)
tables_dir.mkdir(exist_ok=True)

# 2. Configure Pipeline Options
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False          # Off for fast digital PDF reading
pipeline_options.generate_page_images = True  # Required for visual extraction
pipeline_options.images_scale = 2.0      # Sharp 2x resolution for ads/text graphics

# 3. Initialize Docling Converter
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

print(f"🔄 Processing 20-page newspaper: {pdf_path}...")
result = converter.convert(pdf_path)
doc = result.document

# 4. Iterate over every structural element to extract content + metadata
image_idx = 1
table_idx = 1
structured_manifest = []

print("📂 Extracting elements and compiling page metadata...")
for element, level in doc.iterate_items():
    # Safely extract the page number metadata (Docling uses 1-based indexing)
    page_num = element.prov[0].page_no if element.prov else "unknown"
    
    element_data = {
        "type": element.label,
        "page_number": page_num,
        "text_content": getattr(element, "text", "").strip()
    }

    # Context A: Extract Images, Graphics, Ads, and Banners
    if element.label in ["figure", "picture"]:
        try:
            image_obj = element.get_image(doc)
            if image_obj:
                img_name = f"page_{page_num}_img_{image_idx}.png"
                img_path = images_dir / img_name
                image_obj.save(img_path)
                
                element_data["saved_file"] = str(img_path)
                image_idx += 1
        except Exception as e:
            element_data["error"] = f"Failed to save image: {str(e)}"

    # Context B: Extract Tables cleanly
    elif element.label == "table":
        try:
            # Export table to a clean Markdown snippet
            table_markdown = element.export_to_markdown()
            table_name = f"page_{page_num}_table_{table_idx}.md"
            table_path = tables_dir / table_name
            
            with open(table_path, "w", encoding="utf-8") as tf:
                tf.write(table_markdown)
                
            element_data["saved_file"] = str(table_path)
            element_data["text_content"] = table_markdown
            table_idx += 1
        except Exception as e:
            element_data["error"] = f"Failed to export table: {str(e)}"

    structured_manifest.append(element_data)

# 5. Export structural Markdown file with layout intact
markdown_output_path = output_dir / "complete_newspaper_layout.md"
with open(markdown_output_path, "w", encoding="utf-8") as f:
    f.write(doc.export_to_markdown())

# 6. Export Metadata JSON Manifest tracking what is on what page
manifest_path = output_dir / "extraction_manifest.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(structured_manifest, f, indent=4, ensure_ascii=False)

print(f"\n🚀 Success! Everything extracted to folder: '{output_dir}'")
print(f"📝 Full structural text: {markdown_output_path}")
print(f"📊 Detailed page-by-page tracking metadata: {manifest_path}")