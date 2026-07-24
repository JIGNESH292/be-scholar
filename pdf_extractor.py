import io
import requests
from bs4 import BeautifulSoup

def extract_text_from_pdf(pdf_file_source):
    """
    Extract text content from a single PDF file stream or file path.
    """
    text = ""
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_file_source)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(pdf_file_source)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF with PyPDF2: {str(e)}"
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_pdf_chunks(pdf_file_source, chunk_size_chars=4000):
    """
    Extract PDF text in manageable chunks for bulk AI question generation.
    Returns a list of text chunks.
    """
    chunks = []
    current_chunk = ""
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_file_source)
        for page_idx, page in enumerate(reader.pages):
            extracted = page.extract_text() or ""
            if len(current_chunk) + len(extracted) > chunk_size_chars:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = extracted
            else:
                current_chunk += "\n" + extracted
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
    except Exception as e:
        # Fallback raw extraction split
        full_text = extract_text_from_pdf(pdf_file_source)
        for i in range(0, len(full_text), chunk_size_chars):
            chunks.append(full_text[i:i+chunk_size_chars])
            
    return chunks if chunks else [extract_text_from_pdf(pdf_file_source)]

def extract_text_from_url(url):
    """
    Scrape text content from a target webpage using BeautifulSoup.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        return clean_text[:15000]
    except Exception as e:
        return f"Error scraping web page: {str(e)}"
