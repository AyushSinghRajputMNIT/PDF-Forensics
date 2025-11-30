# 🕵️ PDF Forgery Detection using Machine Learning & Deep Learning

### B.Tech Major Project

This project focuses on building an automated system that analyzes PDF documents and determines whether they have been tampered with or forged. The system uses a combination of low-level structural analysis, text forensics, image forensics, and multi-modal ML/DL models.

---

## 🔍 Problem Statement

Design and implement a system that can analyze a given PDF document and determine whether it has been tampered or forged, using Machine Learning and Deep Learning techniques.

PDF documents can be manipulated in various subtle ways—altering metadata, injecting malformed objects, replacing images, modifying text fonts, or editing embedded content. Manual detection is time-consuming and requires expert-level forensic skills.  
This project aims to automate the detection of such manipulations by leveraging data-driven forensics.

---

## 🎯 Objectives

1. **Create a dataset** containing both genuine and tampered/forged PDFs.
2. **Extract low-level structural PDF features** such as:
   - xref tables
   - internal objects
   - streams
   - metadata
3. **Detect structural inconsistencies** indicative of manipulation.
4. **Analyze textual content** for:
   - font mismatches
   - alignment anomalies
   - OCR/text inconsistencies
5. **Analyze embedded images** for editing traces using deep learning models.
6. **Combine multi-modal evidence** (structure + text + image features) using a fusion model.
7. **Output:** probability of forgery and highlight suspicious portions of the PDF.

---
