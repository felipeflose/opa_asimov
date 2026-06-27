import os
import shutil
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from docling.document_converter import DocumentConverter
import logging
import time
import argparse
import unicodedata

# Configure logging
import agent_core
logger = logging.getLogger(__name__)

# Constants (configuraveis via variaveis de ambiente)
_APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = Path(os.environ.get("FLOSE_MBA_SOURCE_DIR", str(_APP_DIR / "vault_temp")))
DEST_BASE_DIR = Path(os.environ.get("FLOSE_MBA_DEST_DIR", str(_APP_DIR / "summaries" / "MBA")))
CRONOGRAMA_PATH = Path(os.environ.get("FLOSE_CRONOGRAMA_PATH", str(_APP_DIR / "vault_temp" / "cronograma.html")))

def normalize(text):
    return unicodedata.normalize('NFC', str(text))

def parse_cronograma(html_path):
    """Parses the HTML schedule to get disciplines and their start dates."""
    if not html_path.exists():
        logging.error(f"Cronograma not found at {html_path}")
        return []

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    disciplines = []
    for div in soup.find_all('div', class_='discipline-info'):
        name = div.find('h3').text.strip()
        start_date_str = ""
        for li in div.find_all('li'):
            if 'Início:' in li.text:
                start_date_str = li.text.replace('Início:', '').strip()
                break
        
        if start_date_str:
            try:
                # Format: DD/MM/YYYY
                start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
                disciplines.append({
                    'name': normalize(name),
                    'start_date': start_date
                })
            except ValueError:
                logging.warning(f"Could not parse date: {start_date_str} for {name}")
    
    # Sort by start date
    disciplines.sort(key=lambda x: x['start_date'])
    return disciplines

def get_discipline_for_date(file_date, disciplines):
    """Returns the discipline name that matches the file date."""
    matching_discipline = "Geral" # Default if no match
    for disc in disciplines:
        if file_date >= disc['start_date']:
            matching_discipline = disc['name']
        else:
            break
    return matching_discipline

def process_single_pdf(pdf_path, disciplines, converter):
    # Get modification time of the file
    mtime = datetime.fromtimestamp(pdf_path.stat().st_mtime)
    
    # Determine discipline
    discipline_name = get_discipline_for_date(mtime, disciplines)
    
    # Define destination directory (Discipline / File Name)
    file_folder_name = normalize(pdf_path.stem)
    dest_dir = DEST_BASE_DIR / discipline_name / file_folder_name
    
    # Use os.makedirs with normalized string
    os.makedirs(normalize(dest_dir), exist_ok=True)
    
    # Define destination file path (.md)
    md_filename = file_folder_name + ".md"
    dest_path = dest_dir / md_filename
    
    # Skip if already exists and is newer than source
    if dest_path.exists():
        if dest_path.stat().st_mtime > pdf_path.stat().st_mtime:
            logging.info(f"Skipping {pdf_path.name} (already converted and up to date)")
            return

    logging.info(f"Converting {pdf_path.name} -> {discipline_name}/{file_folder_name}")
    
    try:
        # Convert PDF to MD using Docling
        result = converter.convert(str(pdf_path))
        md_content = result.document.export_to_markdown()
        
        # Save content
        with open(normalize(dest_path), 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logging.info(f"Successfully saved {md_filename}")
    except Exception as e:
        logging.error(f"Failed to convert {pdf_path.name}: {e}")

def sync_pdfs():
    # 1. Parse cronograma
    disciplines = parse_cronograma(CRONOGRAMA_PATH)
    if not disciplines:
        logging.error("No disciplines found. Check cronograma HTML.")
        return

    # 2. Ensure base directories exist
    os.makedirs(normalize(SOURCE_DIR), exist_ok=True)
    os.makedirs(normalize(DEST_BASE_DIR), exist_ok=True)

    # 3. Create folders for each discipline in both source and destination
    logging.info("Creating discipline folders...")
    for disc in disciplines:
        os.makedirs(normalize(SOURCE_DIR / disc['name']), exist_ok=True)
        os.makedirs(normalize(DEST_BASE_DIR / disc['name']), exist_ok=True)

    # 4. Initialize Docling
    logging.info("Initializing Docling DocumentConverter...")
    converter = DocumentConverter()

    # 5. Process PDFs in source
    pdf_files = list(SOURCE_DIR.rglob("*.pdf"))
    logging.info(f"Found {len(pdf_files)} PDF files in source.")

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(lambda p: process_single_pdf(p, disciplines, converter), pdf_files)

def main():
    parser = argparse.ArgumentParser(description="Sync MBA PDFs to Markdown.")
    parser.add_argument("--watch", action="store_true", help="Run continuously and watch for changes.")
    parser.add_argument("--interval", type=int, default=60, help="Interval in seconds between checks.")
    args = parser.parse_args()

    if args.watch:
        logging.info(f"Watching for changes every {args.interval} seconds...")
        while True:
            try:
                sync_pdfs()
            except Exception as e:
                logging.error(f"Error during sync: {e}")
            time.sleep(args.interval)
    else:
        sync_pdfs()

if __name__ == "__main__":
    main()
