import requests
from bs4 import BeautifulSoup
import os
import time
from typing import List, Dict, Optional

def fetch_form4(cik: str, accession: str, save_dir: str = '../../data/raw') -> str:
    """
    Fetch a Form 4 filing HTML from EDGAR given a company's CIK and accession number.
    Saves the file under `data/raw/<cik>_<accession>.html`.

    Args:
        cik: Company's CIK (Central Index Key)
        accession: SEC accession number (format: XXXXXXXXXX-XX-XXXXXX)
        save_dir: Directory to save the HTML file

    Returns:
        str: Path to the saved HTML file
    """
    # Clean up accession number (remove dashes for URL construction)
    accession_clean = accession.replace('-', '')
    
    # Construct the URL to the actual Form 4 document
    base_url = 'https://www.sec.gov/Archives/edgar/data'
    url = f"{base_url}/{cik}/{accession_clean}/{accession}.txt"
    
    # SEC requires proper user agent identification
    headers = {
        'User-Agent': 'ai-alpha-engine/0.1 (contact@example.com)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    try:
        # Add a small delay to be respectful to SEC servers
        time.sleep(0.1)
        
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Save the file
        filename = os.path.join(save_dir, f"{cik}_{accession}.html")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(resp.text)
        
        print(f"Saved Form 4: {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Form 4: {e}")
        print(f"URL attempted: {url}")
        raise

def parse_form4(html_path: str) -> List[Dict]:
    """
    Parse the saved Form 4 HTML and extract transaction information.

    Args:
        html_path: Path to the saved HTML file

    Returns:
        List[Dict]: List of transaction records
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        
        transactions = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
            key_indicators = ['transaction', 'shares', 'price', 'date', 'code', 'amount']
            if not any(ind in ' '.join(headers) for ind in key_indicators):
                continue

            for row in rows[1:]:
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                if len(cols) >= len(headers):
                    record = {'raw_data': cols, 'num_columns': len(cols)}
                    # Map fields by header name
                    for key in ['date', 'shares', 'price']:
                        if key in headers:
                            idx = headers.index(key)
                            record[key] = cols[idx]
                    transactions.append(record)

        # XML fallback
        if not transactions:
            xml_trans = soup.find_all('transaction')
            for xml in xml_trans:
                rec = {child.name: child.get_text(strip=True) for child in xml.find_all()}
                transactions.append(rec)
        
        print(f"Found {len(transactions)} transaction records")
        return transactions
        
    except Exception as e:
        print(f"Error parsing Form 4: {e}")
        return []

def analyze_form4_structure(html_path: str) -> None:
    """
    Analyze the structure of a Form 4 filing to help with parsing.
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'lxml')
        
        print("=== Structure Analysis ===")
        tables = soup.find_all('table')
        print(f"Tables found: {len(tables)}")
        for i, table in enumerate(tables[:3]):
            rows = table.find_all('tr')
            print(f"Table {i+1} rows: {len(rows)}")
            headers = [cell.get_text(strip=True) for cell in rows[0].find_all(['th','td'])]
            print(f"Headers: {headers}")
    except Exception as e:
        print(f"Error analyzing structure: {e}")

if __name__ == '__main__':
    # Example test
    cik = '0000320193'
    accession = '0001193125-21-038818'
    path = fetch_form4(cik, accession)
    analyze_form4_structure(path)
    records = parse_form4(path)
    for rec in records[:5]:
        print(rec)
