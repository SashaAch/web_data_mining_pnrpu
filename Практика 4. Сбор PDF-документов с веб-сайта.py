import os
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import zipfile
import io
from urllib.parse import urlparse
import easyocr
from pdf2image import convert_from_path

BASE_URL = "https://pstu.ru/"
visited_links = set()

def get_links_from_url(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

    print(f"Fetching links from: {url}")
    soup = BeautifulSoup(resp.content, 'html.parser')

    return [link.get('href') for link in soup.find_all('a') if link.get('href')]

def download_pdf_and_extract_text(url):
    print(f"Downloading and extracting text from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return b"", ""

    pdf_content = response.content
    pdf_io = io.BytesIO(pdf_content)
    try:
        reader = PdfReader(pdf_io)
    except Exception as e:
        print(f"Error reading PDF from {url}: {e}")
        return b"", ""

    text = ""
    for page in range(len(reader.pages)):
        text += reader.pages[page].extract_text() + "\n"

    return pdf_content, text

def recursive_collect_links(base_url, depth):
    try:
        if depth == 0 or not is_valid_url(base_url) or base_url in visited_links:
            return []

        visited_links.add(base_url)
        print(f"Collecting links (Depth {depth}): {base_url}")

        links = get_links_from_url(base_url)
        child_links = []
        for link in links:
            if not link.startswith('http'):
                link = BASE_URL + link
            child_links.extend(recursive_collect_links(link, depth - 1))

    except Exception as e:
        print(f"Error collecting links from {base_url}: {e}")
        return []

    links.extend(child_links)
    return links

def extract_text_from_pdf_with_ocr(pdf_path, reader):
    images = convert_from_path(pdf_path)

    all_text = ""
    for img in images:
        result = reader.readtext(img)
        for detection in result:
            text = detection[1]
            all_text += text + '\n'
    return all_text

def zip_pdf_and_text_from_url(base_url, output_dir, num_doc, depth=1):
    # Если папка для выходного файла не существует, создать её

    reader = easyocr.Reader(['ru', 'en'])

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Zipping PDFs and text files from: {base_url}")

    links = recursive_collect_links(base_url, depth)
    pdf_links = [link for link in links if link.endswith('.pdf')][:num_doc]

    print(len(pdf_links))

    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'a', zipfile.ZIP_DEFLATED) as zipf:
        for pdf_link in pdf_links:

            if not pdf_link.startswith('http'):
                pdf_link = BASE_URL + pdf_link
            pdf_content, text = download_pdf_and_extract_text(pdf_link)

            # Если текст не был извлечен, используем OCR
            if not text:
                with open("temp.pdf", "wb") as temp_pdf:
                    temp_pdf.write(pdf_content)
                text = extract_text_from_pdf_with_ocr("temp.pdf", reader)
                os.remove("temp.pdf")

            pdf_name = pdf_link.split("/")[-1]
            txt_name = pdf_name.replace('.pdf', '.txt')

            zipf.writestr(pdf_name, pdf_content)
            zipf.writestr(txt_name, text.encode("utf-8"))

    zip_filename = os.path.join(output_dir, 'documents.zip')
    with open(zip_filename, 'wb') as f:
        f.write(zip_io.getvalue())

    return zip_filename


def is_valid_url(url):
    try:
        result = urlparse(url)

        # Дополнительные проверки
        if ":" in result.netloc:
            return False

        return all([result.scheme, result.netloc, '.' in result.netloc])
    except ValueError:
        return False


output_dir = r'pdf_zip/'


zip_file_path = zip_pdf_and_text_from_url("https://pstu.ru/sveden/education/", output_dir, 100, depth=1)
print(f"ZIP-архив сохранен в {zip_file_path}")
