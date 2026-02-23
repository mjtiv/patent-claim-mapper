# patent-claim-mapper

## Overview

**patent-claim-mapper** explores whether AI systems can map a user-provided invention description to the claims of issued patents using structured reasoning.

The project focuses on **claim-level technical correspondence detection**, not patent retrieval and not legal infringement determination.

Given:

* an invention description
* a predefined set of patents

the system evaluates whether independent patent claims read on the invention by decomposing claims into elements and comparing them against extracted invention features.

---

## Experimental “Intentional Infringement” Scenario

Example product concept used for testing:

> A computer-implemented platform that receives a user invention description and a set of patent documents, automatically extracts independent claims from the patent documents, parses the claims into hierarchical elements and sub-elements, extracts technical features from the invention description, and compares the extracted features to the claim elements using machine learning or semantic analysis models to generate a claim mapping report indicating matches, missing elements, and confidence scores. The system may visually link mapping results to corresponding claim elements and provide interactive exploration of the mappings.

The invention description is intentionally designed to read on certain patents in the dataset to evaluate discrimination capability.

---

## Dataset

A small controlled corpus is used to create a similarity gradient:

| Role            | Patent No. |
| --------------- | ---------- |
| Anchor          | 9,922,383  |
| Strong neighbor | 9,904,726  |
| Medium neighbor | 8,892,547  |
| Weak neighbor   | 11,100,151 |
| Weak neighbor   | 11,977,722 |
| Outlier         | 6,285,999  |

The goal is for the system to identify stronger correspondence with the anchor patents and minimal correspondence with the outlier.

---

## What Is Being Evaluated

The pipeline tests whether AI can:

1. Read an invention description
2. Extract independent patent claims
3. Decompose claims into elements and sub-elements
4. Determine element-by-element correspondence
5. Identify missing limitations
6. Provide supporting evidence from claim text
7. Estimate confidence of correspondence

This approximates automated **claim chart reasoning**.

---

## Scope and Caveats

* Patents are **pre-selected**.
  The system does not perform patent search or retrieval.
* The objective is **technical correspondence detection**, not legal analysis.
* Outputs are experimental and not suitable for le

