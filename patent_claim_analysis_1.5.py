#!/usr/bin/env python3.10

import os
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from dotenv import load_dotenv
from openai import OpenAI






def get_list_patents(filename):

    """
    Opens the file to get list of the patents

    : Param filename: Name of the file being open
    : Return list_patents: List of the patents to be scraped
    
    """

    #print (filename)

    # Create empty list 
    list_patents = []

    #Open the file
    input_file = open(filename, "r")

    # Loop over lines
    for line in input_file:
        #print (line)
        line = line.rstrip("\n")

        # remove commas
        clean_id = line.replace(",", "")
        #print(clean_id)

        # Adds to the list
        list_patents.append(clean_id)

    input_file.close()
    
    return (list_patents)


def build_google_urls(patent_ids):

    """
    Convert the patent IDs into a google patent address to
    mine the information

    : Param patent_ids: Patent IDs
    : Return urls_list: List of the urls to extract

    """
    urls_list = []

    for pid in patent_ids:
        url = f"https://patents.google.com/patent/US{pid}"
        urls_list.append(url)

    return urls_list


#########################################################################################################################
################################ Scraping and Dumping Patent Information ################################################
#########################################################################################################################


def clean_text(s: str) -> str:
    """
    Normalize whitespace in extracted text.

    This helper is used to clean text pulled from HTML nodes where spacing,
    line breaks, and tabs are often inconsistent due to DOM formatting.

    Behavior:
        • Converts multiple whitespace characters (spaces, tabs, newlines)
          into a single space.
        • Safely handles None or empty input by treating it as an empty string.
        • Removes leading and trailing whitespace.

    Example:
        "  A   method \n for   scoring\tlinks  "
        → "A method for scoring links"

    Parameters
    ----------
    s : str
        Raw text string extracted from HTML or metadata.

    Returns
    -------
    str
        Cleaned, normalized string suitable for storage or downstream parsing.
    """
    s = re.sub(r"\s+", " ", s or "").strip()
    return s


def normalize_abstract(text: str) -> str:
    """
    Takes the abstract section of a patent and removes the
    leading "Abstract" label. Google Patents often embeds the
    word "Abstract" before the actual abstract content, which
    needs to be stripped for clean downstream processing.

    The function also normalizes whitespace to ensure
    consistent formatting.

    Parameters
    ----------
    text : str
        Raw abstract text extracted from the webpage.

    Returns
    -------
    str
        Cleaned abstract text without the leading label.
    """

    if not text:
        return ""

    # Normalize whitespace and remove extra spacing characters
    text = clean_text(text)

    # Remove leading "Abstract" label (case-insensitive)
    text = re.sub(r"^\s*Abstract[:\s-]*", "", text, flags=re.IGNORECASE)

    return text


def scrape_google_patents(url: str) -> dict:

    """
    Retrieve and parse patent data from a Google Patents webpage.

    High-Level Workflow
    -------------------
    1. Download the webpage HTML using an HTTP request.
    2. Parse the HTML into a structured document object using BeautifulSoup.
       This converts raw page text into searchable elements (tags, attributes,
       metadata, etc.).
    3. Locate specific patent fields (title, publication number, abstract,
       claims) by targeting known HTML metadata tags and CSS selectors.
    4. Clean and normalize extracted text using helper functions.
    5. Parse and deduplicate claims by claim number to remove duplicate DOM
       artifacts commonly present on Google Patents pages.
    6. Package the extracted data into a structured dictionary for downstream
       storage or analysis.

    Notes
    -----
    • BeautifulSoup is an HTML parser, not a downloader. The page is first
      retrieved using the `requests` library, then parsed into a searchable
      structure.
    • Selectors such as meta tags, itemprop attributes, and CSS classes are
      identified by inspecting the webpage structure using browser developer
      tools.
    • The function is designed for single-patent acquisition to support an
      “acquire once, analyze many” workflow.

    Parameters
    ----------
    url : str
        Google Patents URL for the patent to retrieve.

    Returns
    -------
    dict
        Structured patent data including title, publication number, abstract,
        claims, and source metadata.
    """

    headers = {
        # Mimic a normal browser a bit (helps reduce trivial blocks)
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    # Title (usually solid)
    title = ""
    t = soup.find("meta", attrs={"name": "DC.title"})
    if t and t.get("content"):
        title = clean_text(t["content"])
    elif soup.title:
        title = clean_text(soup.title.get_text())

    # Publication number (best-effort)
    pub_num = ""
    pub = soup.find("meta", attrs={"scheme": "citation_patent_number"})
    if pub and pub.get("content"):
        pub_num = clean_text(pub["content"])

    # Abstract (often in itemprop="abstract" or a section)
    abstract = ""
    abs_node = soup.find(attrs={"itemprop": "abstract"})
    if abs_node:
        abstract = normalize_abstract(abs_node.get_text(" ", strip=True))
    else:
        md = soup.find("meta", attrs={"name": "description"})
        if md and md.get("content"):
            abstract = normalize_abstract(md["content"])

    # Claims (Google Patents often uses "claim" classes / itemprop, but it varies)
    claims = []
    claim_nodes = soup.select("[itemprop='claims'] .claim") or soup.select(".claims .claim") or soup.select(".claim")
    # Keep it conservative: only grab text that looks like a claim (starts with a number)
    for node in claim_nodes:
        txt = clean_text(node.get_text(" ", strip=True))
        if re.match(r"^\d+\.\s", txt) or re.match(r"^\d+\s", txt):
            claims.append(txt)

    # If that didn’t work, try grabbing claim text blocks
    if not claims:
        alt = soup.select("[itemprop='claims']") or soup.select("section#claims") or []
        for node in alt:
            txt = clean_text(node.get_text(" ", strip=True))
            # crude split heuristic (works sometimes)
            parts = re.split(r"(?=(?:\s|^)\d+\.\s)", " " + txt)
            parts = [clean_text(p) for p in parts if re.match(r"^\d+\.\s", clean_text(p))]
            if parts:
                claims = parts
                break

    # ---- Parse and deduplicate claims by claim number ----
    parsed_claims = []
    seen_nums = set()

    for c in claims:
        m = re.match(r"^(\d+)\.\s*(.*)", c)
        if not m:
            continue

        num = int(m.group(1))
        text = m.group(2).strip()

        if num not in seen_nums:
            parsed_claims.append({
                "claim_number": num,
                "text": text
            })
            seen_nums.add(num)

    claims = parsed_claims


    data = {
        "source": "google_patents",
        "source_url": url,
        "publication_number": pub_num,
        "title": title,
        "abstract": abstract,
        "claims": claims,
        "raw_html_bytes": len(r.content),
    }
    return data


#########################################################################################################################
######################################## Extracting Independent Claims ##################################################
#########################################################################################################################

# -------------------------------------------------------------------------------------------------
# Regular expression used to detect references to other claims.
#
# In U.S. patent practice, dependent claims typically contain phrases like:
#   "The system of claim 1..."
#   "The method according to claim 5..."
#   "As recited in claim 3..."
#
# If such a reference is present, the claim is considered dependent.
# We use this heuristic to identify independent claims by exclusion.
# -------------------------------------------------------------------------------------------------
_DEP_REF = re.compile(r"\b(of|according to|as recited in)\s+claim\s+\d+\b", re.IGNORECASE)

def is_independent_claim(text: str) -> bool:
    """
    Determine whether a claim is independent based on textual heuristics.

    A claim is considered independent if it does NOT contain a reference
    to another claim (e.g., "of claim 1", "according to claim 2").

    Parameters
    ----------
    text : str
        Full claim text.

    Returns
    -------
    bool
        True if the claim appears to be independent, False otherwise.

    Notes
    -----
    This is a heuristic approach. While reliable for most U.S. patents,
    unusual drafting styles or OCR artifacts may cause false positives
    or false negatives.
    """
    return not _DEP_REF.search(text or "")


def extract_independent_claims(data: dict) -> list[dict]:
    """
    Extract independent claims from parsed patent JSON data.

    Parameters
    ----------
    data : dict
        Patent data structure containing a "claims" field.
        Expected format:
            {
                "claims": [
                    {"number": 1, "text": "..."},
                    ...
                ]
            }

    Returns
    -------
    list[dict]
        List of claim dictionaries that are identified as independent.

    Notes
    -----
    The function assumes that claims have already been parsed and stored
    under the "claims" key in the input dictionary.
    """

    return [c for c in data.get("claims", [])
            if is_independent_claim(c.get("text", ""))]

def build_injection_files(in_dir="patent_dump", out_dir="inject_dump"):
    """
    Create simplified injection-ready JSON files containing only
    independent claims and core patent metadata.

    This function reads raw patent JSON files from `in_dir`,
    extracts independent claims, and writes structured payloads
    to `out_dir` for downstream AI processing (e.g., claim mapping,
    similarity analysis, or LLM prompt injection).

    Parameters
    ----------
    in_dir : str or Path, optional
        Directory containing raw patent JSON files.
        Default is "patent_dump".

    out_dir : str or Path, optional
        Output directory where processed injection files will be written.
        Default is "inject_dump".

    Output Structure
    ----------------
    Each output JSON file contains:
        {
            "patent_id": str,
            "source_url": str,
            "title": str,
            "abstract": str,
            "independent_claims": list,
            "independent_claim_count": int
        }

    Workflow
    --------
    1. Iterate through all JSON patent files in the input directory.
    2. Load and parse patent data.
    3. Extract independent claims using heuristic detection.
    4. Construct a reduced payload optimized for AI injection.
    5. Write formatted JSON to the output directory.

    Notes
    -----
    The term "injection" refers to preparing structured data that can be
    safely embedded into LLM prompts or downstream analysis pipelines.
    """

    # Normalize directory paths
    in_dir = Path(in_dir)
    out_dir = Path(out_dir)

    # Ensure output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)

    # Iterate through each patent JSON file
    for fp in sorted(in_dir.glob("*.json")):

        # Load raw patent data
        data = json.loads(fp.read_text(encoding="utf-8"))

        # Extract independent claims using heuristic filter
        indep = extract_independent_claims(data)

         # Build reduced payload optimized for downstream AI workflows
        payload = {
            "patent_id": fp.stem,
            "source_url": data.get("source_url", ""),
            "title": data.get("title", ""),
            "abstract": data.get("abstract", ""),
            "independent_claims": indep,
            "independent_claim_count": len(indep),
        }

        # Output file path mirrors input filename
        out_path = out_dir / fp.name

        # Write formatted JSON for readability and debugging
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        # Console logging for pipeline visibility
        print(f"Wrote: {out_path}  (independent claims: {len(indep)})")


#########################################################################################################################
######################################## Description of Invention  ######################################################
#########################################################################################################################


def get_invention_description(filename):

    """
    Loads the description of the invention

    : Param filename: Name of the file being parsed
    : Return invention_description: Description of the invention (string)
    """

    invention_description = ""

    input_file = open(filename, "r")

    for line in input_file:
        line = line.rstrip("\n")
        invention_description += line + " "

    input_file.close()

    return invention_description

#########################################################################################################################
######################################## Inject the Invention and Claims to AI  #########################################
#########################################################################################################################


# 1) Load environment variables from a local .env file in this directory
#    .env should contain:
#      OPENAI_API_KEY=...
#      OPENAI_MODEL=gpt-4o-mini
load_dotenv()


# 2) Read config from environment variables (with sane defaults)
# ---- Configuration ---------------------------------------------------------
# Load runtime configuration from environment variables.
# Read runtime settings from environment variables.
# This keeps secrets (API keys) and config outside the codebase.
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")

# Fail fast if credentials are missing.
# It's better to stop immediately than make a confusing API call later.
if not API_KEY:
    raise SystemExit(
        "Missing OPENAI_API_KEY. Put it in a .env file or set it in your environment."
    )


# 3) Create an API client
# ---- OpenAI Client ----------------------------------------------------------
# Initialize the OpenAI API client.
# This object handles authentication and sends all requests to the LLM
# (chat completions, embeddings, etc.).
# Think of this as the "brain connection" for the agent.
client = OpenAI(api_key=API_KEY)


def get_claim_analysis_system_prompt() -> str:

    '''
    Claim analysis prompt written as a function because string is
    so big
    '''

    return """You are a strict patent-claim mapping assistant.
Use ONLY the invention description and claim text provided in the user message.
Do NOT assume missing features.

Return JSON ONLY matching this schema:
{
  "patent_id": string,
  "claim_number": integer,
  "claim_text": string,
  "overall_assessment": "LIKELY_MATCH" | "PARTIAL_MATCH" | "NO_MATCH" | "UNCERTAIN",
  "elements": [
    {
      "element_id": string,
      "element_text": string,
      "status": "MATCH" | "MISSING" | "UNCLEAR",
      "invention_evidence": [string, ...],
      "notes": string
    }
  ],
  "missing_elements": [string, ...],
  "summary": string
}

Rules:
- Break the claim into a small number of elements (coarse is fine).
- If an element is not explicitly supported, mark it MISSING (or UNCLEAR if partially implied).
- For MATCH or UNCLEAR, include 1-3 short verbatim snippets from the invention description as evidence.
- For MISSING, invention_evidence must be [].
- Output valid JSON only. No markdown. No extra keys.
"""


def build_claim_analysis_input(invention_text: str, patent_payload: dict, claim: dict) -> str:
    patent_id = patent_payload.get("patent_id", "")
    title = patent_payload.get("title", "")
    abstract = patent_payload.get("abstract", "")
    source_url = patent_payload.get("source_url", "")

    claim_number = claim.get("claim_number", -1)
    claim_text = claim.get("text", "")

    return f"""INVENTION_DESCRIPTION:
<<<
{invention_text}
>>>

PATENT_METADATA:
patent_id: {patent_id}
source_url: {source_url}
title: {title}
abstract: {abstract}

CLAIM:
claim_number: {claim_number}
claim_text:
<<<
{claim_text}
>>>
"""


def call_llm_json(client: OpenAI, system_prompt: str, user_prompt: str) -> dict:
    # Keep it simple: one call, parse JSON, raise if invalid.
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    text = resp.choices[0].message.content.strip()

    # Sometimes models wrap JSON in ```; strip if needed.
    if text.startswith("```"):
        text = text.strip("`")
        # If it still contains a language tag like "json", remove first line
        lines = text.splitlines()
        if lines and lines[0].strip().lower() in ("json", "javascript"):
            text = "\n".join(lines[1:]).strip()

    return json.loads(text)


def analyze_inject_dump(in_dir: str, out_dir: str, invention_text: str, client: OpenAI):

    # Setup the locations of the files
    in_path = Path(in_dir)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Call the long string of the prompt
    system_prompt = get_claim_analysis_system_prompt()

    # Sort through the files
    for fp in sorted(in_path.glob("*.json")):
        patent_payload = json.loads(fp.read_text(encoding="utf-8"))

        # Gets Key Variables
        patent_id = patent_payload.get("patent_id", fp.stem)
        claims = patent_payload.get("independent_claims", [])

        # Loops over the claims
        for claim in claims:
            claim_number = claim.get("claim_number", "NA")

            # Prompt Being Injected in API AI
            user_prompt = build_claim_analysis_input(
                invention_text=invention_text,
                patent_payload=patent_payload,
                claim=claim,
            )

            # Submits the payload to the LLM for analysis
            result = call_llm_json(client, system_prompt, user_prompt)

            # Write one result per claim for easy inspection
            out_file = out_path / f"{patent_id}_claim{claim_number}.json"
            out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

            print(f"Wrote: {out_file}")



#########################################################################################################################
############################################ Main Function ##############################################################
#########################################################################################################################


def summarize_results(results_dir="results_dump", out_csv="summary_report.csv"):

    """

    Writes a full summary report of all the independent patent claims analyzed

    """

    results_dir = Path(results_dir)
    rows = []

    for fp in sorted(results_dir.glob("*.json")):
        d = json.loads(fp.read_text(encoding="utf-8"))

        elements = d.get("elements", [])
        total = len(elements)

        counts = {"MATCH": 0, "UNCLEAR": 0, "MISSING": 0}
        for e in elements:
            s = e.get("status", "")
            if s in counts:
                counts[s] += 1

        match_pct = (counts["MATCH"] / total * 100) if total else 0.0

        rows.append({
            "patent_id": d.get("patent_id", ""),
            "claim_number": d.get("claim_number", ""),
            "overall_assessment": d.get("overall_assessment", ""),
            "elements_total": total,
            "match": counts["MATCH"],
            "unclear": counts["UNCLEAR"],
            "missing": counts["MISSING"],
            "match_%": round(match_pct, 1),
            "result_file": fp.name,
        })

    # Write a simple CSV (no pandas needed)
    header = list(rows[0].keys()) if rows else []
    out_path = Path(out_csv)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(str(r[h]).replace(",", ";") for h in header) + "\n")

    print(f"Wrote summary: {out_path}")



#########################################################################################################################
############################################ Main Function ##############################################################
#########################################################################################################################

def main():

    print ("Starting Claim Analysis Program")
    print ("\n")

    # Asssumes list of patents found in the txt file
    list_patents = get_list_patents("list_of_patents.txt")
    print ("List of Patents to Examine")
    print (list_patents)
    print ("\n")

    # Make a list of URLS for Google Patents Retrieval 
    list_urls = build_google_urls(list_patents)
    print ("URLs to Mine")
    print (list_urls)
    print ("\n")

    # Create Output Directory of Patent Info
    out_dir = Path("patent_dump")
    out_dir.mkdir(parents=True, exist_ok=True)

 
    # Loop over the list of patents and retreives
    # key info from Google Patents
    counter = 0
    for patent in list_patents:
        patent_url = list_urls[counter]
        data = scrape_google_patents(patent_url)

        # Create File Name
        out_path = out_dir / f"{patent}.json"

        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Saved: {out_path}")
        print(f"Title: {data['title']}")
        print(f"Abstract chars: {len(data['abstract'])}")
        print(f"Claims extracted: {len(data['claims'])}")

        counter +=1


    print ("Extracting Independent Claims")
    build_injection_files(in_dir="patent_dump", out_dir="inject_dump")
    print ("Done Extraction")
    print ("\n")

    # Injection Dump in directory "inject_dump"
    # Need to extract the file 
    print ("Loading the Invention Description")
    invention_description = get_invention_description("description_invention.txt")
    #print (invention_description)
    print ("Done Loading the Invention Description")


    print("Running claim analysis")
    analyze_inject_dump(
        in_dir="inject_dump",
        out_dir="results_dump",
        invention_text=invention_description,
        client=client
        )
    print("Done claim analysis")
    print ("\n")

    print("Summarizing Claim Results")
    summarize_results(results_dir="results_dump", out_csv="summary_report.csv")
    print("Done summary")
    print ("\n")

    

    print ("\n")
    print ("Done Running Claim Analysis")
    print ("\n")
    print ("\n")

if __name__ == "__main__":
    
    main()
