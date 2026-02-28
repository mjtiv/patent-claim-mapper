# patent-claim-mapper

## Overview

**patent-claim-mapper** explores whether modern AI systems can perform
structured **claim-level technical correspondence analysis** between an
invention description and issued patent claims.

The project evaluates whether AI can approximate the reasoning process
underlying a **claim chart**, including element decomposition, feature
matching, and identification of missing limitations.

Importantly, this system does **not** perform patent search or legal
infringement analysis. Instead, it focuses on a controlled experimental
setting where patents are pre-selected and the objective is to measure
technical correspondence detection.

------------------------------------------------------------------------

- [Research Objective](#research-objective)
- [Professional Use Disclaimer](#professional-use-disclaimer)
- [Experimental "Intentional Infringement" Scenario](#experimental-intentional-infringement-scenario)
- [Dataset Design](#dataset-design)
- [Patent Status and Public Domain Considerations](#patent-status-and-public-domain-considerations)
- [System Architecture](#system-architecture)
- [How to Run](#how-to-run)
- [Results — Anchor Patent Validation](#results--anchor-patent-validation)
  - [Anchor Patent Performance](#anchor-patent-performance)
  - [Anchor Claim Text](#anchor-claim-text-us-patent-no-9922383---claim-1)
  - [Correspondence Interpretation](#correspondence-interpretation)
  - [Gradient Behavior Across Dataset](#gradient-behavior-across-dataset)
  - [Independent Claim Coverage](#independent-claim-coverage)
  - [Conclusion](#conclusion)
- [Example Output Schema](#example-output-schema)
- [What Is Being Evaluated](#what-is-being-evaluated)
- [Scope and Caveats](#scope-and-caveats)
- [Why This Matters](#why-this-matters)
- [Repository Structure](#repository-structure)
- [Research and Prototype Disclaimer](#research-and-prototype-disclaimer)
- [Methodological Limitations](#methodological-limitations)
- [Intended Use](#intended-use)
- [Author, Contact, and Citation](#author-contact-and-citation)
- [Suggested Citation](#suggested-citation)

------------------------------------------------------------------------

## Research Objective

The central question:

> Can AI reliably determine whether an invention description reads on a patent claim when both are provided explicitly?

This requires multiple reasoning steps:

1. Reading and interpreting an invention description  
2. Extracting independent claims from patents  
3. Decomposing claims into elements and sub-elements  
4. Identifying feature correspondence  
5. Detecting missing limitations  
6. Estimating overall correspondence confidence  

The resulting task approximates automated **claim chart reasoning**.

Because patent claims define the legally enforceable scope of protection, this study focuses on claim language as the primary source of correspondence analysis. Patent specifications, drawings, and prosecution history are not analyzed in this stage in order to maintain a controlled evaluation of claim-to-description matching without introducing additional interpretive complexity.

This claim-centric approach reflects early-stage patent analysis workflows, where practitioners often begin by comparing technical disclosures directly against claim limitations before consulting the full specification.

------------------------------------------------------------------------

## Professional Use Disclaimer

This pipeline is intended to explore whether AI systems can assist with structured claim-to-description correspondence analysis. It does **not** imply that patent agents, patent attorneys, or technical specialists are replaceable.

Patent analysis requires professional judgment, including:

- Claim interpretation and construction
- Legal strategy considerations
- Specification review
- Prosecution history analysis
- Jurisdiction-specific legal standards
- Risk assessment and client counseling

The objective of this work is to evaluate whether certain high-effort, repetitive components of patent workflows — such as initial claim decomposition and preliminary correspondence screening — can be accelerated to support more efficient triage.

In practice, tools of this type are best understood as **decision-support systems** that may help professionals prioritize analysis and allocate time more effectively, allowing greater focus on nuanced legal reasoning and strategic evaluation.

All outputs produced by this pipeline should be treated as experimental and subject to expert review.

------------------------------------------------------------------------

## Experimental "Intentional Infringement" Scenario

A synthetic product concept is intentionally designed to read on certain
patents in the dataset to evaluate discrimination capability.

Example concept:

> A computer-implemented platform that receives a user invention
> description and a set of patent documents, automatically extracts
> independent claims from the patent documents, parses the claims into
> hierarchical elements and sub-elements, extracts technical features
> from the invention description, and compares the extracted features to
> the claim elements using machine learning or semantic analysis models
> to generate a claim mapping report indicating matches, missing
> elements, and confidence scores. The system may visually link mapping
> results to corresponding claim elements and provide interactive
> exploration of the mappings.

This allows measurement of whether the system correctly identifies:

-   Strong correspondence with target patents\
-   Weaker correspondence with unrelated patents

------------------------------------------------------------------------

## Dataset Design

A small controlled patent corpus is used to create a similarity
gradient:

  Role              Patent No.
  ----------------- ------------
  Anchor            9,922,383
  Strong neighbor   9,904,726
  Medium neighbor   8,892,547
  Weak neighbor     11,100,151
  Weak neighbor     11,977,722
  Outlier           6,285,999

The expected behavior:

-   Highest correspondence → Anchor patents\
-   Moderate correspondence → Related patents\
-   Minimal correspondence → Outlier

This structure enables evaluation of ranking and discrimination
capability.

------------------------------------------------------------------------

## Patent Status and Public Domain Considerations

The primary anchor patent used in this study (U.S. Patent No. 9,922,383) is listed as **expired** according to publicly available records.

The use of an expired patent provides several advantages for experimental evaluation:

- The claimed subject matter is no longer under enforceable patent protection.
- Analysis can be conducted using publicly available materials without commercial or legal sensitivity.
- The experiment can focus purely on technical correspondence behavior rather than real-world infringement risk.

Because the patent has expired, the results presented in this repository should be interpreted solely as a methodological demonstration of claim-to-description mapping capability using public-domain material.

No commercial product or system described here is intended to practice or implement the patented invention.

------------------------------------------------------------------------

## System Architecture

The pipeline follows an **acquire once, analyze many** workflow:

### 1. Patent Acquisition

Patents are retrieved from Google Patents and parsed into structured
JSON:

-   Title\
-   Abstract\
-   Claims\
-   Metadata

### 2. Independent Claim Extraction

Independent claims are identified using textual heuristics (absence of
claim dependency references).

### 3. Injection Payload Construction

Simplified JSON payloads are created containing:

-   Patent metadata\
-   Independent claims\
-   Abstract

These payloads are optimized for AI analysis.

### 4. Claim Mapping Analysis

For each independent claim, the system:

-   Breaks the claim into coarse elements\

-   Compares elements against invention features\

-   Labels each element:

    -   MATCH\
    -   MISSING\
    -   UNCLEAR

-   Generates structured reasoning output in JSON format.

### 5. Result Aggregation

Outputs are summarized into a CSV report including:

-   Match percentages\
-   Element counts\
-   Overall assessments

------------------------------------------------------------------------

## How to Run

### Prerequisites

- Python **3.10+**
- An OpenAI API key
- Internet access (for scraping Google Patents)

### Install Dependencies

Create a virtual environment (recommended), then install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

If you do not yet have a `requirements.txt`, the script uses at least:

- openai
- python-dotenv
- requests
- beautifulsoup4
- lxml

### Required Input Files

Create these files in the same directory as the script:

1) **list_of_patents.txt**  
One patent number per line (commas optional). Example:

```text
9,922,383
9,904,726
8,892,547
11,100,151
11,977,722
6,285,999
```

2) **description_invention.txt**  
Plain-text description of the invention / product concept you want to map against the claims.

3) **.env**  
Environment variables for the model and key:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

> Note: The analysis prompt instructs the model to use only the invention description and claim text for correspondence reasoning. Patent title/abstract are included as metadata context.

### Run the Pipeline

Run:

```bash
python patent_claim_analysis_1.5.py
```

### Outputs

The script creates the following directories/files:

- `patent_dump/`  
  Raw scraped patent JSON (title, abstract, full claims, metadata)

- `inject_dump/`  
  Reduced per-patent payloads containing **independent claims** + metadata

- `results_dump/`  
  One JSON result per **independent claim** (element breakdown + match status)

- `summary_report.csv`  
  Aggregate summary across all analyzed independent claims (match counts and match %)

### Typical Workflow Notes

- The system analyzes **all independent claims** for each patent (not just Claim 1).
- If scraping fails for a patent due to page layout differences or rate limiting, re-run or reduce the list size and retry.

------------------------------------------------------------------------

# Results --- Anchor Patent Validation

## Anchor Patent Performance

The system was evaluated on a controlled patent corpus designed to
produce a similarity gradient between the invention description and
selected patents.

The primary objective was to determine whether the pipeline could
correctly identify stronger correspondence with the anchor patents while
minimizing correspondence with unrelated patents.

The strongest result was observed for **U.S. Patent No. 9,922,383 ---
Claim 1**, which served as the anchor patent intentionally targeted by
the synthetic invention description.

The system produced:

-   **Overall assessment:** LIKELY_MATCH\
-   **Elements evaluated:** 9\
-   **Matched elements:** 9\
-   **Missing elements:** 0\
-   **Match percentage:** 100%

This represents complete element-level correspondence between the
invention description and the claim.

Notably, the model identified explicit textual evidence from the
invention description for each claim element, indicating that the
pipeline successfully performed:

-   Claim decomposition\
-   Feature extraction\
-   Element-level mapping\
-   Evidence grounding

The perfect correspondence score for the anchor claim demonstrates that
the system can detect strong technical alignment when present.

------------------------------------------------------------------------

## Anchor Claim Text (U.S. Patent No. 9,922,383 --- Claim 1)

To provide transparency and allow independent evaluation of the
correspondence analysis, the full text of the highest-scoring claim is
reproduced below.

> **Claim 1.** A system for analyzing patent claims, the system
> comprising:\
> at least one input device in communication with at least one computer
> and at least one output device, wherein the at least one computer is
> capable of storing, modifying, outputting, and retrieving information
> via an electronic network from the at least one input device and the
> at least one output device;\
> at least one database, the database in network communication with the
> at least one computer; and\
> software installed and capable of running on the at least one computer
> for automatically:\
> importing patent claims via the electronic network based upon the user
> inputted information;\
> parsing the imported patent claims hierarchically, wherein each
> independent claim is parsed into its invention sub-elements, wherein
> an invention sub-element is a parsed patent invention element or a
> step of the independent patent invention claim, and wherein the
> hierarchically parsed patent claims comprises hierarchical elements
> and sub-elements;\
> generating a hierarchical claims diagram comprising a textual claim
> content associated with each patent claim, and\
> outputting the hierarchical claims diagram, wherein, for each patent
> claim, the hierarchical claims diagram shows the parsed claims in an
> interactive format that is operable to dynamically expand and compress
> the textual claim content, according to the hierarchy of the imported
> patent claims;\
> receiving sub-element selections from the input device;\
> analyzing the sub-element selections for technology content;\
> searching the at least one database in real-time via the network for
> matching technology content;\
> receiving a study purpose;\
> analyzing in real-time via the network a matching technology content
> record for matching study purpose;\
> retrieving in real-time from the Internet the matching technology and
> study purpose content;\
> displaying on a GUI matching technology and study purpose content
> thumbnail images beside the patent claims diagram; and\
> visually linking the thumbnail images to their sub-element.

------------------------------------------------------------------------

## Correspondence Interpretation

The invention description used in this experiment explicitly included
functionality involving:

-   Automated claim import and parsing\
-   Hierarchical decomposition into claim elements\
-   Mapping invention features to claim elements\
-   Generation of claim mapping outputs\
-   Visual linking between elements and results

These features align closely with the structural and functional
limitations recited in Claim 1, particularly those relating to:

-   Hierarchical claim parsing\
-   Diagram generation and visualization\
-   Element selection and analysis\
-   Database searching and retrieval\
-   Visual linkage of results to claim sub-elements

The system identified supporting textual evidence for all claim
elements, resulting in:

-   **9 / 9 elements matched**\
-   **0 missing elements**\
-   **Overall assessment:** LIKELY_MATCH

This complete correspondence supports the validity of the pipeline's
ability to detect strong technical alignment when present.

------------------------------------------------------------------------

## Gradient Behavior Across Dataset

![Claim Mapping Summary](figures/summary_report_results.png)

The broader dataset exhibited the expected similarity gradient:

- **Anchor (9,922,383):** LIKELY_MATCH / highest scores  
- **Strong Neighbor (9,904,726):** High PARTIAL_MATCH (~70–75%)  
- **Medium Neighbor (8,892,547):** Moderate PARTIAL_MATCH  
- **Weak Neighbors:** NO_MATCH  
- **Outlier (6,285,999):** Predominantly NO_MATCH  

This pattern indicates that the system demonstrates discriminative capability across patents with varying conceptual similarity.

------------------------------------------------------------------------

## Independent Claim Coverage

All independent claims for each patent were analyzed in this study rather than limiting evaluation to Claim 1.

This approach is important because patent applicants frequently include:

- Broad independent claims later in the claim set  
- Multiple statutory classes (system, method, apparatus)  
- Alternative scope formulations across independent claims  

As a result, the strongest technical correspondence for a given patent may not always occur in the first independent claim.

By evaluating **all independent claims**, the pipeline avoids structural bias introduced by claim ordering and more accurately reflects real-world patent analysis workflows, where practitioners review the entire independent claim set when assessing correspondence or risk.

The results table therefore represents the highest-confidence correspondence observed across the independent claims of each patent.

------------------------------------------------------------------------

## Conclusion

The experiment demonstrates that structured AI pipelines can:

-   Map invention descriptions to patent claim elements\
-   Detect missing limitations\
-   Rank correspondence strength across patents

The successful identification of Claim 1 of U.S. 9,922,383 as the top
match provides strong preliminary validation of the approach.


------------------------------------------------------------------------

## Example Output Schema

``` json
{
  "patent_id": "9922383",
  "claim_number": 1,
  "overall_assessment": "LIKELY_MATCH",
  "elements": [
    {
      "element_id": "E1",
      "element_text": "...",
      "status": "MATCH",
      "invention_evidence": ["..."],
      "notes": "..."
    }
  ],
  "missing_elements": [],
  "summary": "..."
}
```

------------------------------------------------------------------------

## What Is Being Evaluated

The project measures whether AI can perform:

-   Structured claim decomposition\
-   Evidence-grounded reasoning\
-   Element-level correspondence detection\
-   Missing limitation identification\
-   Confidence estimation

This represents a step toward automated **technical claim chart
generation**.

------------------------------------------------------------------------

## Scope and Caveats

Important limitations:

-   Patents are **pre-selected** (no search component).\
-   Results are **experimental**.\
-   Outputs are **not legal advice**.\
-   The system does **not determine infringement**.\
-   Claim interpretation is simplified compared to real legal analysis.

The purpose is to evaluate technical feasibility, not legal conclusions.

------------------------------------------------------------------------

## Why This Matters

Claim mapping is one of the most time-consuming tasks in patent
practice, including:

-   Freedom-to-operate analysis\
-   Invalidity analysis\
-   Litigation preparation\
-   Patent drafting support\
-   Competitive intelligence

Demonstrating reliable AI assistance in this domain could significantly
impact legal workflows.

------------------------------------------------------------------------

## Repository Structure

    patent_dump/        Raw scraped patent data
    inject_dump/        Independent claim payloads
    results_dump/       AI analysis outputs
    summary_report.csv  Aggregated results

------------------------------------------------------------------------

## Research and Prototype Disclaimer

This repository is provided for **research, educational, and prototyping purposes**.

The system implements an experimental pipeline for structured claim-to-description correspondence analysis using large language models. It is intended to explore whether AI-assisted workflows can support early-stage patent analysis tasks such as claim decomposition and preliminary technical mapping.

This project does **not** provide:

- Legal advice
- Infringement determinations
- Patentability opinions
- Freedom-to-operate conclusions
- Claim construction or legal interpretation

All outputs should be considered **experimental artifacts** requiring expert review.

Patent analysis in professional practice involves substantially more rigor than is implemented here, including:

- Specification and drawing analysis
- Prosecution history review
- Legal claim construction standards (e.g., Phillips framework)
- Jurisdiction-specific doctrine
- Prior art analysis and search methodology
- Strategic and commercial risk assessment

This prototype intentionally simplifies many of these factors in order to isolate and evaluate a narrower technical question: whether structured AI pipelines can assist with claim-element correspondence detection when claims and descriptions are provided explicitly.

------------------------------------------------------------------------

## Methodological Limitations

The current implementation represents an early-stage research prototype and does not establish scientific validity or performance guarantees.

Limitations include:

- Small controlled dataset
- Synthetic invention descriptions
- Simplified claim parsing heuristics
- Absence of specification context
- Limited statistical evaluation
- Dependence on stochastic model behavior

Future work could incorporate more rigorous evaluation frameworks, including:

- Larger benchmark datasets
- Blind validation sets
- Inter-annotator agreement comparisons
- Error taxonomy analysis
- Ablation studies
- Statistical performance metrics
- Human expert baseline comparisons

Accordingly, results presented in this repository should be interpreted as **proof-of-concept demonstrations**, not validated performance claims.

------------------------------------------------------------------------

## Intended Use

Tools of this type are best understood as **decision-support or triage aids** that may help professionals prioritize analysis and allocate effort more efficiently.

They are not substitutes for qualified patent practitioners.

------------------------------------------------------------------------

## Author, Contact, and Citation

This repository was prepared by **M. Joseph Tomlinson IV**, Ph.D., Registered U.S. Patent Agent (USPTO Reg. No. 83,522), based on professional experience and independent research in patent analysis workflows and AI-assisted technical evaluation.

Portions of the implementation and documentation were developed with the assistance of AI-based tools and subsequently reviewed by the author. The content is intended for **educational, research, and prototyping purposes** and reflects retrospective analysis of publicly available materials.

Feedback, corrections, and discussion are welcome. Please open an issue in this repository or contact the author directly.

**Contact**  
Email: mjtiv@udel.edu  

------------------------------------------------------------------------

## Suggested Citation

If referencing this work in academic, technical, or professional contexts, please cite:

> Tomlinson, M.J. (2026). *Patent Claim Mapper: Evaluating AI-Based Technical Correspondence Detection Between Invention Descriptions and Patent Claims.* GitHub Repository.  
> https://github.com/mjtiv/patent-claim-mapper
