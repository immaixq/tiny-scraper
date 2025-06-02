import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib.parse

BASE_URL = "https://sso.agc.gov.sg"
INITIAL_BROWSE_PATH = "/Browse/Act/Current/All"
PAGE_SIZE = 500
SORT_PARAMS = "SortBy=Title&SortOrder=ASC"
REQUEST_TIMEOUT = 45
DELAY_BETWEEN_REQUESTS = 2 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_full_url(path):
    """Constructs an absolute URL from a base URL and a path."""
    return urllib.parse.urljoin(BASE_URL, path)


def parse_page_count(soup):

    page_count_element = soup.select_one("div.page-count")
    if not page_count_element:
        page_count_element = soup.select_one(
            "div.page-count-wrapper > div.page-count"
        )  # Alternative selector observed

    if page_count_element:
        page_count_text = page_count_element.get_text(strip=True)
        match = re.search(r"in (\d+) pages", page_count_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        elif "results" in page_count_text:
            act_rows = soup.select("table.table.browse-list > tbody > tr")
            if act_rows:
                return 1
            else:
                print(
                    f"Interpreting as 0 pages of actual items despite text: {page_count_text}"
                )
                return 0
        else:
            print(
                f"Could not determine total pages from text: '{page_count_text}'. Assuming 1 page if items exist."
            )
            act_rows = soup.select("table.table.browse-list > tbody > tr")
            return 1 if act_rows else 0
    else:
        print("Page count element not found. Checking for items to assume 1 page.")
        act_rows = soup.select("table.table.browse-list > tbody > tr")
        return 1 if act_rows else 0


def extract_data_from_soup(soup):
    """
    Extracts Act titles and PDF URLs from a BeautifulSoup object.
    """
    acts_on_page = []
    act_rows = soup.select("table.table.browse-list > tbody > tr")

    if not act_rows:
        list_panel = soup.select_one("#listPanel table.table.browse-list > tbody")
        if list_panel:
            act_rows = list_panel.select("tr")

    for row_index, row in enumerate(act_rows):
        act_title = "N/A"
        pdf_url = "N/A"

        title_tag = row.select_one("td:first-child a.non-ajax")
        if title_tag and title_tag.string:
            act_title = title_tag.get_text(strip=True)

        # Extract PDF URL
        pdf_tag = row.select_one(
            'td.hidden-xs a.non-ajax.file-download[href*="ViewType=Pdf"]'
        )

        if pdf_tag and pdf_tag.has_attr("href"):
            relative_pdf_url = pdf_tag["href"]
            pdf_url = get_full_url(relative_pdf_url) 

        if act_title != "N/A" or pdf_url != "N/A":
            if act_title == "N/A" and pdf_url == "N/A":  # Skip if both are N/A
                print(f"Skipping row {row_index+1} due to missing title and PDF URL.")
                continue
            acts_on_page.append({"Act Title": act_title, "PDF URL": pdf_url})
    return acts_on_page


def scrapy_scrape():
    """
    Scrapes Act titles and their PDF URLs from the Singapore Statutes Online website,
    handling pagination.
    """
    all_acts_data = []

    first_page_url = (
        f"{BASE_URL}{INITIAL_BROWSE_PATH}?PageSize={PAGE_SIZE}&{SORT_PARAMS}"
    )

    print(f"Fetching first page: {first_page_url}")
    try:
        response = requests.get(
            first_page_url, headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching first page: {e}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    acts_from_first_page = extract_data_from_soup(soup)
    all_acts_data.extend(acts_from_first_page)
    print(f"Found {len(acts_from_first_page)} acts on the first page.")

    total_pages = parse_page_count(soup)
    print(f"Total pages to scrape (with PageSize={PAGE_SIZE}): {total_pages}")

    if total_pages == 0 and not all_acts_data:
        print("No results found on the first page and total pages is 0. Exiting.")
        return all_acts_data

    # --- Subsequent Pages (if any) ---
    if total_pages > 1:
        for page_num in range(2, total_pages + 1):
            page_index_in_url = page_num - 1
            page_url = f"{BASE_URL}{INITIAL_BROWSE_PATH}/{page_index_in_url}?PageSize={PAGE_SIZE}&{SORT_PARAMS}"

            print(f"Fetching page {page_num}/{total_pages}: {page_url}")
            time.sleep(DELAY_BETWEEN_REQUESTS)

            try:
                response = requests.get(
                    page_url, headers=HEADERS, timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page_num}: {e}. Skipping this page.")
                continue  # Skip to next page

            page_soup = BeautifulSoup(response.content, "html.parser")
            acts_from_this_page = extract_data_from_soup(page_soup)
            all_acts_data.extend(acts_from_this_page)
            print(f"Found {len(acts_from_this_page)} acts on page {page_num}.")

    print(f"\nTotal acts extracted from all pages: {len(all_acts_data)}")
    return all_acts_data


def save_to_csv(data, filename="acts_data_revised.csv"):
    """
    Saves the extracted data to a CSV file.
    """
    if not data:
        print("No data to save.")
        return

    df = pd.DataFrame(data)
    try:
        df.to_csv(filename, index=False, encoding="utf-8")
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")


if __name__ == "__main__":
    print("Starting the web scraper...")
    extracted_data = scrapy_scrape()

    if extracted_data is not None:
        if extracted_data:
            save_to_csv(extracted_data)
        else:
            print("No data was extracted by the scraper.")
    else:
        print("Scraping process failed to return data.")
    print("Scraper finished.")
