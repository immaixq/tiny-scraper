# tiny-scraper
## Description
This is a demonstation of extracting data from a publicly accessible website, the website chosen is: https://sso.agc.gov.sg/Browse/Act/Current, which contains structured list based data.

## Project Structure
```bash
.
├── main.py
├── pylock.toml
├── pyproject.toml
├── README.md
├── requirements.txt
├── src
│   ├── acts_data_revised.csv
│   └── tiny_scrape.py

```

## Setup Instructions

Follow these steps to set up your local environment.

1. Clone the Repository 

```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Set Up Virtual Environment & Install Dependencies
Option A: Using uv
- Install uv (if not already installed):
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
```
- Create and activate the virtual environment:

```bash
uv venv {venv name}
source {venv path}
```
- Install dependencies using uv:
```bash
uv pip install -r requirements.txt
```

Option B: Using venv 
```bash
python -m venv .venv
pip install -r requirements.txt

```
## How to Run

1. Navigate to your project's src directory in the terminal.
2. Run the following script:

```bash
cd src
python tiny_scrape.py
```

Upon successful completion, the scraper will generate a CSV file: acts_data_revised.csv



