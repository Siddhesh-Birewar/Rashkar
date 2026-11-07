"""
Generator script to produce the 10 representative soil test reports
and ground truth JSON files in services/api/tests/evaluation/soil_reports_corpus/.
"""

import os
import json
import io
import hashlib
from PIL import Image, ImageDraw
from fpdf import FPDF

CORPUS_DIR = os.path.dirname(os.path.abspath(__file__)) + "/soil_reports_corpus"
os.makedirs(CORPUS_DIR, exist_ok=True)


def create_tc01_digital_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "DISTRICT SOIL TESTING LABORATORY, PUNE", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "SOIL HEALTH CARD REPORT", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Laboratory: District Soil Testing Laboratory, Pune", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Farmer Name: Vitthalrao Patil", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sample ID: MH-PUN-2024-8841", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Report Date: 15/04/2024", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Collection Date: 05/04/2024", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sampling Depth: 0-15 cm", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sampling Point: Plot 4B, North Field", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Village: Baramati, Taluka: Baramati, District: Pune, State: Maharashtra", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Table Header
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(15, 7, "Sr No", border=1)
    pdf.cell(65, 7, "Parameter", border=1)
    pdf.cell(25, 7, "Result", border=1)
    pdf.cell(25, 7, "Unit", border=1)
    pdf.cell(35, 7, "Rating", border=1)
    pdf.cell(30, 7, "Method", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    rows = [
        ("1", "pH (1:2.5)", "7.65", "pH", "Slightly Alkaline", "1:2.5 water"),
        ("2", "Electrical Conductivity (EC)", "0.38", "dS/m", "Normal", "Conductivity Bridge"),
        ("3", "Organic Carbon (OC)", "0.52", "%", "Medium", "Walkley-Black"),
        ("4", "Available Nitrogen (N)", "195.0", "kg/ha", "Low", "Alk. Permanganate"),
        ("5", "Available Phosphorus (P2O5)", "16.4", "kg/ha", "Medium", "Olsen Method"),
        ("6", "Available Potassium (K2O)", "340.0", "kg/ha", "High", "Flame Photometer"),
        ("7", "Available Sulphur (S)", "8.2", "ppm", "Deficient", "0.15% CaCl2"),
        ("8", "Available Zinc (Zn)", "0.55", "ppm", "Deficient", "DTPA Extractable"),
        ("9", "Available Iron (Fe)", "3.8", "ppm", "Deficient", "DTPA Extractable"),
        ("10", "Available Manganese (Mn)", "6.2", "ppm", "Sufficient", "DTPA Extractable"),
        ("11", "Available Copper (Cu)", "1.4", "ppm", "Sufficient", "DTPA Extractable"),
        ("12", "Available Boron (B)", "0.45", "ppm", "Deficient", "Hot Water"),
    ]
    for r in rows:
        pdf.cell(15, 6, r[0], border=1)
        pdf.cell(65, 6, r[1], border=1)
        pdf.cell(25, 6, r[2], border=1)
        pdf.cell(25, 6, r[3], border=1)
        pdf.cell(35, 6, r[4], border=1)
        pdf.cell(30, 6, r[5], border=1, new_x="LMARGIN", new_y="NEXT")

    out_pdf = os.path.join(CORPUS_DIR, "tc01_shc_pune_digital.pdf")
    pdf.output(out_pdf)

    gt = {
        "document_id": "TC-01",
        "document_filename": "tc01_shc_pune_digital.pdf",
        "expected_document_type": "text_pdf",
        "expected_metadata": {
            "laboratory_name": "District Soil Testing Laboratory, Pune",
            "sample_id": "MH-PUN-2024-8841",
            "farmer_name": "Vitthalrao Patil",
            "report_date": "2024-04-15",
            "collection_date": "2024-04-05",
            "sample_depth": "0-15 cm",
            "sampling_point": "Plot 4B, North Field",
            "village": "Baramati",
            "taluka": "Baramati",
            "district": "Pune",
            "state": "Maharashtra",
        },
        "expected_parameters": {
            "soil_ph": {"value": 7.65, "unit": "pH", "is_ambiguous": False},
            "electrical_conductivity": {"value": 0.38, "unit": "dS/m", "is_ambiguous": False},
            "organic_carbon": {"value": 0.52, "unit": "%", "is_ambiguous": False},
            "available_nitrogen": {"value": 195.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_phosphorus": {"value": 16.4, "unit": "kg/ha", "is_ambiguous": False},
            "available_potassium": {"value": 340.0, "unit": "kg/ha", "is_ambiguous": False},
            "sulphur": {"value": 8.2, "unit": "ppm", "is_ambiguous": False},
            "zinc": {"value": 0.55, "unit": "ppm", "is_ambiguous": False},
            "iron": {"value": 3.8, "unit": "ppm", "is_ambiguous": False},
            "manganese": {"value": 6.2, "unit": "ppm", "is_ambiguous": False},
            "copper": {"value": 1.4, "unit": "ppm", "is_ambiguous": False},
            "boron": {"value": 0.45, "unit": "ppm", "is_ambiguous": False},
        },
    }
    with open(os.path.join(CORPUS_DIR, "tc01_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc02_scanned_pdf():
    # Create image representing a scanned printed sheet with stamp
    w, h = 800, 1050
    img = Image.new("RGB", (w, h), color=(250, 249, 246))
    d = ImageDraw.Draw(img)

    text_md = """
# KRISHI VIGYAN KENDRA SOIL TESTING LAB, BARAMATI
## SOIL HEALTH REPORT

Laboratory: Krishi Vigyan Kendra Soil Testing Lab, Baramati
Farmer Name: Ramesh Shinde
Sample ID: KVK-BAR-2024-102
Report Date: 22/03/2024
Collection Date: 10/03/2024
Sampling Depth: 0-20 cm
Village: Malegaon, Taluka: Baramati, District: Pune

| Sr. No. | Parameter | Result | Unit | Rating |
| :--- | :--- | :--- | :--- | :--- |
| 1 | pH (1:2.5) | 7.80 | pH | Normal |
| 2 | Electrical Conductivity (EC) | 0.45 | dS/m | Normal |
| 3 | Organic Carbon (OC) | 0.48 | % | Medium |
| 4 | Available Nitrogen (N) | 210.0 | kg/ha | Low |
| 5 | Available Phosphorus (P2O5) | 18.0 | kg/ha | Medium |
| 6 | Available Potassium (K2O) | 310.0 | kg/ha | High |
| 7 | Available Sulphur (S) | 9.5 | ppm | Deficient |
| 8 | Available Zinc (Zn) | 0.62 | ppm | Sufficient |
"""
    # Draw simple visual representation
    d.text((40, 40), "KRISHI VIGYAN KENDRA SOIL TESTING LAB, BARAMATI", fill=(20, 20, 20))
    d.text((40, 70), "SOIL ANALYSIS CERTIFICATE", fill=(40, 40, 40))
    d.text((40, 110), "Laboratory: Krishi Vigyan Kendra Soil Testing Lab, Baramati", fill=(0, 0, 0))
    d.text((40, 135), "Farmer Name: Ramesh Shinde", fill=(0, 0, 0))
    d.text((40, 160), "Sample ID: KVK-BAR-2024-102", fill=(0, 0, 0))
    d.text((40, 185), "Report Date: 22/03/2024 | Collection Date: 10/03/2024", fill=(0, 0, 0))
    d.text((40, 210), "Sampling Depth: 0-20 cm | Village: Malegaon, Taluka: Baramati, District: Pune", fill=(0, 0, 0))

    # Draw table border & rows
    d.rectangle([(40, 250), (740, 600)], outline=(80, 80, 80), width=2)
    d.line([(40, 280), (740, 280)], fill=(80, 80, 80), width=2)
    d.text((50, 258), "Sr. No.", fill=(0, 0, 0))
    d.text((120, 258), "Parameter", fill=(0, 0, 0))
    d.text((380, 258), "Result", fill=(0, 0, 0))
    d.text((480, 258), "Unit", fill=(0, 0, 0))
    d.text((580, 258), "Rating", fill=(0, 0, 0))

    rows = [
        ("1", "pH (1:2.5)", "7.80", "pH", "Normal"),
        ("2", "Electrical Conductivity (EC)", "0.45", "dS/m", "Normal"),
        ("3", "Organic Carbon (OC)", "0.48", "%", "Medium"),
        ("4", "Available Nitrogen (N)", "210.0", "kg/ha", "Low"),
        ("5", "Available Phosphorus (P2O5)", "18.0", "kg/ha", "Medium"),
        ("6", "Available Potassium (K2O)", "310.0", "kg/ha", "High"),
        ("7", "Available Sulphur (S)", "9.5", "ppm", "Deficient"),
        ("8", "Available Zinc (Zn)", "0.62", "ppm", "Sufficient"),
    ]
    y = 295
    for r in rows:
        d.text((50, y), r[0], fill=(0, 0, 0))
        d.text((120, y), r[1], fill=(0, 0, 0))
        d.text((380, y), r[2], fill=(0, 0, 0))
        d.text((480, y), r[3], fill=(0, 0, 0))
        d.text((580, y), r[4], fill=(0, 0, 0))
        y += 35

    # Simulated circular stamp
    d.ellipse([(550, 650), (700, 800)], outline=(0, 50, 180), width=3)
    d.text((570, 715), "KVK VERIFIED", fill=(0, 50, 180))

    img.info["report_text"] = text_md

    out_pdf = os.path.join(CORPUS_DIR, "tc02_kvk_baramati_scanned.pdf")
    img.save(out_pdf, "PDF", resolution=150.0)

    gt = {
        "document_id": "TC-02",
        "document_filename": "tc02_kvk_baramati_scanned.pdf",
        "expected_document_type": "scanned_pdf",
        "expected_metadata": {
            "laboratory_name": "Krishi Vigyan Kendra Soil Testing Lab, Baramati",
            "sample_id": "KVK-BAR-2024-102",
            "farmer_name": "Ramesh Shinde",
            "report_date": "2024-03-22",
            "collection_date": "2024-03-10",
            "sample_depth": "0-20 cm",
            "village": "Malegaon",
            "taluka": "Baramati",
            "district": "Pune",
        },
        "expected_parameters": {
            "soil_ph": {"value": 7.80, "unit": "pH", "is_ambiguous": False},
            "electrical_conductivity": {"value": 0.45, "unit": "dS/m", "is_ambiguous": False},
            "organic_carbon": {"value": 0.48, "unit": "%", "is_ambiguous": False},
            "available_nitrogen": {"value": 210.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_phosphorus": {"value": 18.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_potassium": {"value": 310.0, "unit": "kg/ha", "is_ambiguous": False},
            "sulphur": {"value": 9.5, "unit": "ppm", "is_ambiguous": False},
            "zinc": {"value": 0.62, "unit": "ppm", "is_ambiguous": False},
        },
    }
    with open(os.path.join(CORPUS_DIR, "tc02_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc03_mpkv_report():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "MPKV AGRICULTURAL UNIVERSITY SOIL TESTING LABORATORY, RAHURI", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "COMPREHENSIVE SOIL FERTILITY EVALUATION", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Laboratory: MPKV Agricultural University Soil Testing Laboratory, Rahuri", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Farmer Name: Anand Deshmukh", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sample ID: MPKV-SL-2024-551", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Report Date: 10/05/2024", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Collection Date: 28/04/2024", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sampling Depth: 0-15 cm", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sampling Point: Sector 3, Canal Block", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(15, 7, "Sr No", border=1)
    pdf.cell(60, 7, "Parameter", border=1)
    pdf.cell(25, 7, "Result", border=1)
    pdf.cell(25, 7, "Unit", border=1)
    pdf.cell(65, 7, "Analytical Method", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    rows = [
        ("1", "pH (1:2.5)", "8.10", "pH", "1:2.5 water suspension"),
        ("2", "Electrical Conductivity (EC)", "0.28", "dS/m", "Conductivity bridge"),
        ("3", "Organic Carbon (OC)", "0.65", "%", "Walkley-Black wet oxidation"),
        ("4", "Available Nitrogen (N)", "245.0", "kg/ha", "Alkaline permanganate"),
        ("5", "Available Phosphorus (P2O5)", "22.5", "kg/ha", "Olsen spectrophotometric"),
        ("6", "Available Potassium (K2O)", "410.0", "kg/ha", "Neutral 1N ammonium acetate flame"),
        ("7", "Available Zinc (Zn)", "0.75", "ppm", "DTPA AAS method"),
        ("8", "Available Iron (Fe)", "4.60", "ppm", "DTPA AAS method"),
        ("9", "Available Manganese (Mn)", "7.50", "ppm", "DTPA AAS method"),
        ("10", "Available Copper (Cu)", "1.80", "ppm", "DTPA AAS method"),
        ("11", "Available Boron (B)", "0.58", "ppm", "Azomethine-H hot water"),
    ]
    for r in rows:
        pdf.cell(15, 6, r[0], border=1)
        pdf.cell(60, 6, r[1], border=1)
        pdf.cell(25, 6, r[2], border=1)
        pdf.cell(25, 6, r[3], border=1)
        pdf.cell(65, 6, r[4], border=1, new_x="LMARGIN", new_y="NEXT")

    out_pdf = os.path.join(CORPUS_DIR, "tc03_mpkv_rahuri_report.pdf")
    pdf.output(out_pdf)

    gt = {
        "document_id": "TC-03",
        "document_filename": "tc03_mpkv_rahuri_report.pdf",
        "expected_document_type": "text_pdf",
        "expected_metadata": {
            "laboratory_name": "MPKV Agricultural University Soil Testing Laboratory, Rahuri",
            "sample_id": "MPKV-SL-2024-551",
            "farmer_name": "Anand Deshmukh",
            "report_date": "2024-05-10",
            "collection_date": "2024-04-28",
            "sample_depth": "0-15 cm",
            "sampling_point": "Sector 3, Canal Block",
        },
        "expected_parameters": {
            "soil_ph": {"value": 8.10, "unit": "pH", "is_ambiguous": False},
            "electrical_conductivity": {"value": 0.28, "unit": "dS/m", "is_ambiguous": False},
            "organic_carbon": {"value": 0.65, "unit": "%", "is_ambiguous": False},
            "available_nitrogen": {"value": 245.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_phosphorus": {"value": 22.5, "unit": "kg/ha", "is_ambiguous": False},
            "available_potassium": {"value": 410.0, "unit": "kg/ha", "is_ambiguous": False},
            "zinc": {"value": 0.75, "unit": "ppm", "is_ambiguous": False},
            "iron": {"value": 4.60, "unit": "ppm", "is_ambiguous": False},
            "manganese": {"value": 7.50, "unit": "ppm", "is_ambiguous": False},
            "copper": {"value": 1.80, "unit": "ppm", "is_ambiguous": False},
            "boron": {"value": 0.58, "unit": "ppm", "is_ambiguous": False},
        },
    }
    with open(os.path.join(CORPUS_DIR, "tc03_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc04_image_jpeg():
    w, h = 800, 1000
    img = Image.new("RGB", (w, h), color=(245, 245, 240))
    d = ImageDraw.Draw(img)

    text_md = """
# DISTRICT SOIL TESTING LABORATORY, PUNE
## SOIL HEALTH CARD

Laboratory: District Soil Testing Laboratory, Pune
Farmer Name: Sanjay More
Sample ID: MH-PUN-2024-9102
Report Date: 12/06/2024
Collection Date: 01/06/2024
Sampling Depth: 0-15 cm
Village: Daund, Taluka: Daund, District: Pune

| Sr. No. | Parameter | Result | Unit | Rating |
| :--- | :--- | :--- | :--- | :--- |
| 1 | pH (1:2.5) | 7.40 | pH | Normal |
| 2 | Electrical Conductivity (EC) | 0.32 | dS/m | Normal |
| 3 | Organic Carbon (OC) | 0.58 | % | Medium |
| 4 | Available Nitrogen (N) | 185.0 | kg/ha | Low |
| 5 | Available Phosphorus (P2O5) | 14.8 | kg/ha | Medium |
| 6 | Available Potassium (K2O) | 290.0 | kg/ha | Medium |
| 7 | Available Sulphur (S) | 11.0 | ppm | Sufficient |
| 8 | Available Zinc (Zn) | 0.48 | ppm | Deficient |
"""
    d.text((40, 40), "DISTRICT SOIL TESTING LABORATORY, PUNE", fill=(10, 10, 10))
    d.text((40, 70), "SOIL HEALTH CARD - FARMER COPY", fill=(30, 30, 30))
    d.text((40, 110), "Laboratory: District Soil Testing Laboratory, Pune", fill=(0, 0, 0))
    d.text((40, 135), "Farmer Name: Sanjay More", fill=(0, 0, 0))
    d.text((40, 160), "Sample ID: MH-PUN-2024-9102", fill=(0, 0, 0))
    d.text((40, 185), "Report Date: 12/06/2024 | Collection Date: 01/06/2024", fill=(0, 0, 0))
    d.text((40, 210), "Sampling Depth: 0-15 cm | Village: Daund, Taluka: Daund, District: Pune", fill=(0, 0, 0))

    d.rectangle([(40, 250), (740, 600)], outline=(50, 50, 50), width=2)
    d.line([(40, 280), (740, 280)], fill=(50, 50, 50), width=2)
    d.text((50, 258), "Sr. No.", fill=(0, 0, 0))
    d.text((120, 258), "Parameter", fill=(0, 0, 0))
    d.text((380, 258), "Result", fill=(0, 0, 0))
    d.text((480, 258), "Unit", fill=(0, 0, 0))
    d.text((580, 258), "Rating", fill=(0, 0, 0))

    rows = [
        ("1", "pH (1:2.5)", "7.40", "pH", "Normal"),
        ("2", "Electrical Conductivity (EC)", "0.32", "dS/m", "Normal"),
        ("3", "Organic Carbon (OC)", "0.58", "%", "Medium"),
        ("4", "Available Nitrogen (N)", "185.0", "kg/ha", "Low"),
        ("5", "Available Phosphorus (P2O5)", "14.8", "kg/ha", "Medium"),
        ("6", "Available Potassium (K2O)", "290.0", "kg/ha", "Medium"),
        ("7", "Available Sulphur (S)", "11.0", "ppm", "Sufficient"),
        ("8", "Available Zinc (Zn)", "0.48", "ppm", "Deficient"),
    ]
    y = 295
    for r in rows:
        d.text((50, y), r[0], fill=(0, 0, 0))
        d.text((120, y), r[1], fill=(0, 0, 0))
        d.text((380, y), r[2], fill=(0, 0, 0))
        d.text((480, y), r[3], fill=(0, 0, 0))
        d.text((580, y), r[4], fill=(0, 0, 0))
        y += 35

    img.info["report_text"] = text_md

    out_jpg = os.path.join(CORPUS_DIR, "tc04_soil_card_photo.jpg")
    img.save(out_jpg, "JPEG", quality=95)

    gt = {
        "document_id": "TC-04",
        "document_filename": "tc04_soil_card_photo.jpg",
        "expected_document_type": "image_jpeg",
        "expected_metadata": {
            "laboratory_name": "District Soil Testing Laboratory, Pune",
            "sample_id": "MH-PUN-2024-9102",
            "farmer_name": "Sanjay More",
            "report_date": "2024-06-12",
            "collection_date": "2024-06-01",
            "sample_depth": "0-15 cm",
            "village": "Daund",
            "taluka": "Daund",
            "district": "Pune",
        },
        "expected_parameters": {
            "soil_ph": {"value": 7.40, "unit": "pH", "is_ambiguous": False},
            "electrical_conductivity": {"value": 0.32, "unit": "dS/m", "is_ambiguous": False},
            "organic_carbon": {"value": 0.58, "unit": "%", "is_ambiguous": False},
            "available_nitrogen": {"value": 185.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_phosphorus": {"value": 14.8, "unit": "kg/ha", "is_ambiguous": False},
            "available_potassium": {"value": 290.0, "unit": "kg/ha", "is_ambiguous": False},
            "sulphur": {"value": 11.0, "unit": "ppm", "is_ambiguous": False},
            "zinc": {"value": 0.48, "unit": "ppm", "is_ambiguous": False},
        },
    }
    with open(os.path.join(CORPUS_DIR, "tc04_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc05_image_png_glare():
    w, h = 800, 950
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    text_md = """
# PUNE AGRO ANALYTICAL LABORATORY
## SOIL REPORT

Laboratory: Pune Agro Analytical Laboratory
Farmer Name: Dnyaneshwar Jagtap
Sample ID: PAL-2024-338
Report Date: 18/05/2024
Sampling Depth: 0-15 cm

| Sr. No. | Parameter | Result | Unit | Rating |
| :--- | :--- | :--- | :--- | :--- |
| 1 | pH (1:2.5) | 7.90 | pH | Normal |
| 2 | Electrical Conductivity (EC) | 0.52 | dS/m | Normal |
| 3 | Organic Carbon (OC) | 0.41 | % | Low |
| 4 | Available Nitrogen (N) | 210* (glare) | kg/ha | Low |
| 5 | Available Phosphorus (P2O5) | 12.0 | kg/ha | Low |
| 6 | Available Potassium (K2O) | 380.0 | kg/ha | High |
"""
    d.text((40, 40), "PUNE AGRO ANALYTICAL LABORATORY", fill=(0, 0, 0))
    d.text((40, 70), "Laboratory: Pune Agro Analytical Laboratory", fill=(0, 0, 0))
    d.text((40, 95), "Farmer Name: Dnyaneshwar Jagtap", fill=(0, 0, 0))
    d.text((40, 120), "Sample ID: PAL-2024-338", fill=(0, 0, 0))
    d.text((40, 145), "Report Date: 18/05/2024", fill=(0, 0, 0))
    d.text((40, 170), "Sampling Depth: 0-15 cm", fill=(0, 0, 0))

    # Table
    d.rectangle([(40, 220), (740, 520)], outline=(0, 0, 0), width=1)
    d.line([(40, 255), (740, 255)], fill=(0, 0, 0), width=1)
    d.text((50, 230), "Parameter", fill=(0, 0, 0))
    d.text((380, 230), "Result", fill=(0, 0, 0))
    d.text((480, 230), "Unit", fill=(0, 0, 0))

    rows = [
        ("pH (1:2.5)", "7.90", "pH"),
        ("Electrical Conductivity (EC)", "0.52", "dS/m"),
        ("Organic Carbon (OC)", "0.41", "%"),
        ("Available Nitrogen (N)", "210* (glare)", "kg/ha"),
        ("Available Phosphorus (P2O5)", "12.0", "kg/ha"),
        ("Available Potassium (K2O)", "380.0", "kg/ha"),
    ]
    y = 270
    for r in rows:
        d.text((50, y), r[0], fill=(0, 0, 0))
        d.text((380, y), r[1], fill=(0, 0, 0))
        d.text((480, y), r[2], fill=(0, 0, 0))
        y += 40

    # Draw white glare spot over Nitrogen cell
    d.ellipse([(360, 370), (450, 410)], fill=(255, 255, 255), outline=(240, 240, 240))
    d.text((370, 385), "210* (glare)", fill=(180, 180, 180))

    img.info["report_text"] = text_md

    out_png = os.path.join(CORPUS_DIR, "tc05_lab_report_glare.png")
    img.save(out_png, "PNG")

    gt = {
        "document_id": "TC-05",
        "document_filename": "tc05_lab_report_glare.png",
        "expected_document_type": "image_png",
        "expected_metadata": {
            "laboratory_name": "Pune Agro Analytical Laboratory",
            "sample_id": "PAL-2024-338",
            "farmer_name": "Dnyaneshwar Jagtap",
            "report_date": "2024-05-18",
            "sample_depth": "0-15 cm",
        },
        "expected_parameters": {
            "soil_ph": {"value": 7.90, "unit": "pH", "is_ambiguous": False},
            "electrical_conductivity": {"value": 0.52, "unit": "dS/m", "is_ambiguous": False},
            "organic_carbon": {"value": 0.41, "unit": "%", "is_ambiguous": False},
            "available_nitrogen": {"value": 210.0, "unit": "kg/ha", "is_ambiguous": True},
            "available_phosphorus": {"value": 12.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_potassium": {"value": 380.0, "unit": "kg/ha", "is_ambiguous": False},
        },
        "expected_ambiguity_count": 1,
    }
    with open(os.path.join(CORPUS_DIR, "tc05_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc06_handwritten_pdf():
    w, h = 800, 1000
    img = Image.new("RGB", (w, h), color=(252, 250, 242))
    d = ImageDraw.Draw(img)

    text_md = """
# BARAMATI RURAL SOIL TESTING CAMP
## FIELD TESTING REPORT

Laboratory: Baramati Rural Soil Testing Camp
Farmer Name: Babasaheb Ghadge
Sample ID: CAMP-BAR-044
Report Date: 14/02/2024
Sampling Depth: 0-15 cm

| Sr. No. | Parameter | Result | Unit |
| :--- | :--- | :--- | :--- |
| 1 | pH | 8.40 | pH |
| 2 | EC | 0.65 | dS/m |
| 3 | Organic Carbon | 0.35 | % |
| 4 | Available Nitrogen | 160.0 | kg/ha |
| 5 | Available Phosphorus | 11.2 | kg/ha |
| 6 | Available Potassium | 260.0 | kg/ha |
| 7 | Zinc | 0.38* (smudged) | ppm |
"""
    d.text((40, 40), "BARAMATI RURAL SOIL TESTING CAMP", fill=(20, 20, 20))
    d.text((40, 70), "Laboratory: Baramati Rural Soil Testing Camp", fill=(0, 0, 0))
    d.text((40, 95), "Farmer Name: Babasaheb Ghadge", fill=(0, 0, 0))
    d.text((40, 120), "Sample ID: CAMP-BAR-044", fill=(0, 0, 0))
    d.text((40, 145), "Report Date: 14/02/2024", fill=(0, 0, 0))
    d.text((40, 170), "Sampling Depth: 0-15 cm", fill=(0, 0, 0))

    d.rectangle([(40, 210), (740, 560)], outline=(100, 100, 100), width=1)
    d.line([(40, 245), (740, 245)], fill=(100, 100, 100), width=1)

    d.text((50, 220), "Parameter", fill=(0, 0, 0))
    d.text((380, 220), "Handwritten Result", fill=(0, 0, 0))
    d.text((550, 220), "Unit", fill=(0, 0, 0))

    rows = [
        ("pH", "8.40", "pH"),
        ("EC", "0.65", "dS/m"),
        ("Organic Carbon", "0.35", "%"),
        ("Available Nitrogen", "160.0", "kg/ha"),
        ("Available Phosphorus", "11.2", "kg/ha"),
        ("Available Potassium", "260.0", "kg/ha"),
        ("Zinc", "0.38* (smudged)", "ppm"),
    ]
    y = 260
    for r in rows:
        d.text((50, y), r[0], fill=(0, 0, 0))
        d.text((380, y), r[1], fill=(0, 0, 150))  # blue ink simulation
        d.text((550, y), r[2], fill=(0, 0, 0))
        y += 40

    img.info["report_text"] = text_md

    out_pdf = os.path.join(CORPUS_DIR, "tc06_handwritten_soil_card.pdf")
    img.save(out_pdf, "PDF", resolution=150.0)

    gt = {
        "document_id": "TC-06",
        "document_filename": "tc06_handwritten_soil_card.pdf",
        "expected_document_type": "scanned_pdf",
        "expected_metadata": {
            "laboratory_name": "Baramati Rural Soil Testing Camp",
            "sample_id": "CAMP-BAR-044",
            "farmer_name": "Babasaheb Ghadge",
            "report_date": "2024-02-14",
            "sample_depth": "0-15 cm",
        },
        "expected_parameters": {
            "soil_ph": {"value": 8.40, "unit": "pH", "is_ambiguous": False},
            "electrical_conductivity": {"value": 0.65, "unit": "dS/m", "is_ambiguous": False},
            "organic_carbon": {"value": 0.35, "unit": "%", "is_ambiguous": False},
            "available_nitrogen": {"value": 160.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_phosphorus": {"value": 11.2, "unit": "kg/ha", "is_ambiguous": False},
            "available_potassium": {"value": 260.0, "unit": "kg/ha", "is_ambiguous": False},
            "zinc": {"value": 0.38, "unit": "ppm", "is_ambiguous": True},
        },
        "expected_ambiguity_count": 1,
    }
    with open(os.path.join(CORPUS_DIR, "tc06_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc07_multi_depth_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "ICAR-NRC ON POMEGRANATE SOIL TESTING LABORATORY, SOLAPUR", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "ORCHARD PROFILE SOIL TEST REPORT", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Laboratory: ICAR-NRC on Pomegranate Soil Testing Laboratory, Solapur", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Farmer Name: Ashok Kadam", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sample ID: NRCP-SOIL-2024-77", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Report Date: 20/04/2024", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Crop: Pomegranate (Bhagawa Variety)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(65, 7, "Parameter", border=1)
    pdf.cell(35, 7, "0-15 cm", border=1)
    pdf.cell(35, 7, "15-30 cm", border=1)
    pdf.cell(30, 7, "Unit", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    rows = [
        ("pH (1:2.5)", "7.70", "8.00", "pH"),
        ("Electrical Conductivity (EC)", "0.42", "0.58", "dS/m"),
        ("Organic Carbon (OC)", "0.55", "0.38", "%"),
        ("Available Nitrogen (N)", "220.0", "140.0", "kg/ha"),
        ("Available Phosphorus (P2O5)", "19.5", "11.0", "kg/ha"),
        ("Available Potassium (K2O)", "360.0", "280.0", "kg/ha"),
    ]
    for r in rows:
        pdf.cell(65, 6, r[0], border=1)
        pdf.cell(35, 6, r[1], border=1)
        pdf.cell(35, 6, r[2], border=1)
        pdf.cell(30, 6, r[3], border=1, new_x="LMARGIN", new_y="NEXT")

    out_pdf = os.path.join(CORPUS_DIR, "tc07_multi_depth_orchard.pdf")
    pdf.output(out_pdf)

    gt = {
        "document_id": "TC-07",
        "document_filename": "tc07_multi_depth_orchard.pdf",
        "expected_document_type": "text_pdf",
        "expected_metadata": {
            "laboratory_name": "ICAR-NRC on Pomegranate Soil Testing Laboratory, Solapur",
            "sample_id": "NRCP-SOIL-2024-77",
            "farmer_name": "Ashok Kadam",
            "report_date": "2024-04-20",
        },
        "expected_parameters_multi_depth": [
            {"parameter_key": "soil_ph", "depth": "0-15 cm", "value": 7.70, "unit": "pH"},
            {"parameter_key": "soil_ph", "depth": "15-30 cm", "value": 8.00, "unit": "pH"},
            {"parameter_key": "electrical_conductivity", "depth": "0-15 cm", "value": 0.42, "unit": "dS/m"},
            {"parameter_key": "electrical_conductivity", "depth": "15-30 cm", "value": 0.58, "unit": "dS/m"},
            {"parameter_key": "organic_carbon", "depth": "0-15 cm", "value": 0.55, "unit": "%"},
            {"parameter_key": "organic_carbon", "depth": "15-30 cm", "value": 0.38, "unit": "%"},
            {"parameter_key": "available_nitrogen", "depth": "0-15 cm", "value": 220.0, "unit": "kg/ha"},
            {"parameter_key": "available_nitrogen", "depth": "15-30 cm", "value": 140.0, "unit": "kg/ha"},
            {"parameter_key": "available_phosphorus", "depth": "0-15 cm", "value": 19.5, "unit": "kg/ha"},
            {"parameter_key": "available_phosphorus", "depth": "15-30 cm", "value": 11.0, "unit": "kg/ha"},
            {"parameter_key": "available_potassium", "depth": "0-15 cm", "value": 360.0, "unit": "kg/ha"},
            {"parameter_key": "available_potassium", "depth": "15-30 cm", "value": 280.0, "unit": "kg/ha"},
        ],
    }
    with open(os.path.join(CORPUS_DIR, "tc07_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc08_total_nitrogen_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "STATE AGRICULTURAL RESEARCH INSTITUTE LAB", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "RESEARCH PLOT SOIL CHEMICAL ASSAY", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Laboratory: State Agricultural Research Institute Lab", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Farmer Name: Kisanrao Shinde", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sample ID: SARI-RES-2024-819", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Report Date: 02/05/2024", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sampling Depth: 0-15 cm", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(15, 7, "Sr No", border=1)
    pdf.cell(70, 7, "Parameter", border=1)
    pdf.cell(30, 7, "Result", border=1)
    pdf.cell(30, 7, "Unit", border=1)
    pdf.cell(40, 7, "Method", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    rows = [
        ("1", "Soil pH (1:2.5)", "7.20", "pH", "Glass electrode"),
        ("2", "Electrical Conductivity (EC)", "0.25", "dS/m", "Conductivity cell"),
        ("3", "Organic Carbon (OC)", "0.72", "%", "Walkley-Black"),
        ("4", "Total Nitrogen", "0.08", "%", "Micro-Kjeldahl digestion"),
        ("5", "Available Phosphorus (P2O5)", "24.0", "kg/ha", "Olsen method"),
        ("6", "Available Potassium (K2O)", "420.0", "kg/ha", "Neutral ammonium acetate"),
    ]
    for r in rows:
        pdf.cell(15, 6, r[0], border=1)
        pdf.cell(70, 6, r[1], border=1)
        pdf.cell(30, 6, r[2], border=1)
        pdf.cell(30, 6, r[3], border=1)
        pdf.cell(40, 6, r[4], border=1, new_x="LMARGIN", new_y="NEXT")

    out_pdf = os.path.join(CORPUS_DIR, "tc08_total_nitrogen_report.pdf")
    pdf.output(out_pdf)

    gt = {
        "document_id": "TC-08",
        "document_filename": "tc08_total_nitrogen_report.pdf",
        "expected_document_type": "text_pdf",
        "expected_metadata": {
            "laboratory_name": "State Agricultural Research Institute Lab",
            "sample_id": "SARI-RES-2024-819",
            "farmer_name": "Kisanrao Shinde",
            "report_date": "2024-05-02",
            "sample_depth": "0-15 cm",
        },
        "expected_parameters": {
            "soil_ph": {"value": 7.20, "unit": "pH", "is_ambiguous": False},
            "electrical_conductivity": {"value": 0.25, "unit": "dS/m", "is_ambiguous": False},
            "organic_carbon": {"value": 0.72, "unit": "%", "is_ambiguous": False},
            "total_nitrogen": {"value": 0.08, "unit": "%", "is_ambiguous": False},
            "available_nitrogen": {"value": None, "unit": None, "extraction_status": "NOT_REPORTED"},
            "available_phosphorus": {"value": 24.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_potassium": {"value": 420.0, "unit": "kg/ha", "is_ambiguous": False},
        },
        "safeguard_checks": ["Safeguard 3: Available Nitrogen must remain NOT_REPORTED"],
    }
    with open(os.path.join(CORPUS_DIR, "tc08_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc09_oxide_notation_jpg():
    w, h = 800, 1000
    img = Image.new("RGB", (w, h), color=(248, 248, 245))
    d = ImageDraw.Draw(img)

    text_md = """
# MAHARASHTRA AGRO CHEMICAL TESTING LABORATORY
## SOIL ANALYSIS REPORT

Laboratory: Maharashtra Agro Chemical Testing Laboratory
Farmer Name: Gorakhnath Patil
Sample ID: MAC-2024-8890
Report Date: 25/06/2024
Sampling Depth: 0-15 cm

| Sr. No. | Parameter | Result | Unit |
| :--- | :--- | :--- | :--- |
| 1 | pH | 7.50 | pH |
| 2 | EC | 0.34 | dS/m |
| 3 | Organic Carbon | 0.60 | % |
| 4 | Available Nitrogen | 230.0 | kg/ha |
| 5 | Available Phosphorus (P206) | 15.5 | kg/ha |
| 6 | Available Potassium (K2O) | 325.0 | kg/ha |
| 7 | Available Sulphur (S) | 12.5 | ppm |
| 8 | Available Zinc (Zn) | 0.68 | ppm |
"""
    d.text((40, 40), "MAHARASHTRA AGRO CHEMICAL TESTING LABORATORY", fill=(0, 0, 0))
    d.text((40, 70), "Laboratory: Maharashtra Agro Chemical Testing Laboratory", fill=(0, 0, 0))
    d.text((40, 95), "Farmer Name: Gorakhnath Patil", fill=(0, 0, 0))
    d.text((40, 120), "Sample ID: MAC-2024-8890", fill=(0, 0, 0))
    d.text((40, 145), "Report Date: 25/06/2024", fill=(0, 0, 0))
    d.text((40, 170), "Sampling Depth: 0-15 cm", fill=(0, 0, 0))

    d.rectangle([(40, 210), (740, 580)], outline=(80, 80, 80), width=1)
    d.line([(40, 245), (740, 245)], fill=(80, 80, 80), width=1)
    d.text((50, 220), "Parameter", fill=(0, 0, 0))
    d.text((420, 220), "Result", fill=(0, 0, 0))
    d.text((540, 220), "Unit", fill=(0, 0, 0))

    rows = [
        ("pH", "7.50", "pH"),
        ("EC", "0.34", "dS/m"),
        ("Organic Carbon", "0.60", "%"),
        ("Available Nitrogen", "230.0", "kg/ha"),
        ("Available Phosphorus (P206)", "15.5", "kg/ha"),
        ("Available Potassium (K2O)", "325.0", "kg/ha"),
        ("Available Sulphur (S)", "12.5", "ppm"),
        ("Available Zinc (Zn)", "0.68", "ppm"),
    ]
    y = 260
    for r in rows:
        d.text((50, y), r[0], fill=(0, 0, 0))
        d.text((420, y), r[1], fill=(0, 0, 0))
        d.text((540, y), r[2], fill=(0, 0, 0))
        y += 38

    img.info["report_text"] = text_md

    out_jpg = os.path.join(CORPUS_DIR, "tc09_oxide_notation_report.jpg")
    img.save(out_jpg, "JPEG", quality=95)

    gt = {
        "document_id": "TC-09",
        "document_filename": "tc09_oxide_notation_report.jpg",
        "expected_document_type": "image_jpeg",
        "expected_metadata": {
            "laboratory_name": "Maharashtra Agro Chemical Testing Laboratory",
            "sample_id": "MAC-2024-8890",
            "farmer_name": "Gorakhnath Patil",
            "report_date": "2024-06-25",
            "sample_depth": "0-15 cm",
        },
        "expected_parameters": {
            "soil_ph": {"value": 7.50, "unit": "pH", "is_ambiguous": False},
            "electrical_conductivity": {"value": 0.34, "unit": "dS/m", "is_ambiguous": False},
            "organic_carbon": {"value": 0.60, "unit": "%", "is_ambiguous": False},
            "available_nitrogen": {"value": 230.0, "unit": "kg/ha", "is_ambiguous": False},
            "available_phosphorus": {"value": 15.5, "unit": "kg/ha", "is_ambiguous": True},
            "available_potassium": {"value": 325.0, "unit": "kg/ha", "is_ambiguous": False},
            "sulphur": {"value": 12.5, "unit": "ppm", "is_ambiguous": False},
            "zinc": {"value": 0.68, "unit": "ppm", "is_ambiguous": False},
        },
        "expected_ambiguity_count": 1,
    }
    with open(os.path.join(CORPUS_DIR, "tc09_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


def create_tc10_fertilizer_invoice_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "BARAMATI AGRO KRUSHI SEVA KENDRA", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "TAX INVOICE / CASH MEMO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Invoice No: INV-2024-9912", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Customer: Shri Dilip Pawar", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Date: 14/05/2024", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "GSTIN: 27AABCB1234F1Z5", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(15, 7, "Item", border=1)
    pdf.cell(85, 7, "Description", border=1)
    pdf.cell(25, 7, "Qty", border=1)
    pdf.cell(30, 7, "Rate (Rs)", border=1)
    pdf.cell(35, 7, "Total (Rs)", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    rows = [
        ("1", "IFFCO Neem Coated Urea 45kg bag", "4 Bags", "266.50", "1,066.00"),
        ("2", "KRIBHCO DAP 18:46:0 50kg bag", "2 Bags", "1,350.00", "2,700.00"),
        ("3", "Muriate of Potash (MOP) 50kg bag", "1 Bag", "1,650.00", "1,650.00"),
    ]
    for r in rows:
        pdf.cell(15, 6, r[0], border=1)
        pdf.cell(85, 6, r[1], border=1)
        pdf.cell(25, 6, r[2], border=1)
        pdf.cell(30, 6, r[3], border=1)
        pdf.cell(35, 6, r[4], border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(155, 8, "Total Invoice Amount:", border=1, align="R")
    pdf.cell(35, 8, "Rs 5,416.00", border=1, new_x="LMARGIN", new_y="NEXT", align="C")

    out_pdf = os.path.join(CORPUS_DIR, "tc10_fertilizer_invoice.pdf")
    pdf.output(out_pdf)

    gt = {
        "document_id": "TC-10",
        "document_filename": "tc10_fertilizer_invoice.pdf",
        "expected_document_type": "text_pdf",
        "is_negative_control": True,
        "expected_status": "FAILED",
        "expected_parameters_count": 0,
    }
    with open(os.path.join(CORPUS_DIR, "tc10_ground_truth.json"), "w") as f:
        json.dump(gt, f, indent=2)


if __name__ == "__main__":
    create_tc01_digital_pdf()
    create_tc02_scanned_pdf()
    create_tc03_mpkv_report()
    create_tc04_image_jpeg()
    create_tc05_image_png_glare()
    create_tc06_handwritten_pdf()
    create_tc07_multi_depth_pdf()
    create_tc08_total_nitrogen_pdf()
    create_tc09_oxide_notation_jpg()
    create_tc10_fertilizer_invoice_pdf()
    print("All 10 soil test reports and ground truth files generated successfully.")
