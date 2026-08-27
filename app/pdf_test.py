from utils import load_pdf, chunk_pdf_pages

pdf_path = "data/documents/sample.pdf"

pages = load_pdf(pdf_path)

print("Total pages extracted:", len(pages))

chunks = chunk_pdf_pages(
    pages,
    chunk_size=50
)

print("Total chunks:", len(chunks))

for index, chunk in enumerate(chunks[:5], start=1):
    print(f"\nChunk {index}")
    print("Page:", chunk["page"])
    print("Text:", chunk["text"])