"""
Deterministic parser for soil laboratory reports.
Parses Markdown tables and key-value lines, extracting sample metadata
and mapping parameters to canonical nutrient keys.
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .models import (
    SoilReportMetadata,
    ExtractedSoilMeasurement,
    CANONICAL_NUTRIENT_KEYS,
    PARAMETER_ALIASES,
    ParameterExtractionStatus,
    MeasurementVerificationStatus,
)


# Parameter definition: (canonical_key, regex_pattern, is_exclusive_negative)
PARAMETER_PATTERNS = [
    # Total Nitrogen (checked before available nitrogen to avoid partial matches)
    ("total_nitrogen", re.compile(r"\b(total\s*nitrogen|total\s*n\b|n\s*\(total\)|एकूण\s*नत्र)", re.IGNORECASE)),
    
    # Available Nitrogen
    ("available_nitrogen", re.compile(r"\b(available\s*nitrogen|avail(?:able|\.)?\s*n\b|mineral\s*nitrogen|उपलब्ध\s*नत्र|\bनत्र\b)", re.IGNORECASE)),
    
    # Organic Matter (SOM) (checked before OC to prevent SOM matching OC)
    ("organic_matter", re.compile(r"\b(organic\s*matter|soil\s*organic\s*matter|s\.?o\.?m\.?\b|सेंद्रिय\s*पदार्थ)", re.IGNORECASE)),
    
    # Organic Carbon (SOC)
    ("organic_carbon", re.compile(r"\b(organic\s*carbon|s\.?o\.?c\.?\b|o\.?c\.?\b|सेंद्रिय\s*कर्ब)", re.IGNORECASE)),
    
    # Soil pH (exclude Phosphorus and telephone/contact patterns)
    ("soil_ph", re.compile(r"(?:\bsoil\s*p[hH]\b|(?<!\bphone\s)(?<!\btel\s)(?<!\bmob\s)(?<!\boff\s)(?<!\bcall\s)(?<!\bcontact\s)\bp[hH]\b(?!\.|\s*no\b|\s*num\b|\s*#|\s*:\s*\d{3,}|\s*-\s*\d{3,}|\s*\d{3,}|\s*osphorus|\s*os\b|\s*hate)|\bp[hH]\s*\(1:2\.?5?\)|\bसामू\b)", re.IGNORECASE)),
    
    # Electrical Conductivity (EC)
    ("electrical_conductivity", re.compile(r"\b(electrical\s*conductivity|e\.?c\.?\b|conductivity|विद्युत\s*वाहकता|\bईसी\b)", re.IGNORECASE)),
    
    # Available Phosphorus (P2O5 / Avail P) - note P206 is OCR confusion
    ("available_phosphorus", re.compile(r"\b(available\s*phosphorus|avail(?:able|\.)?\s*p\b|p2o5|p205|p206|p2o|उपलब्ध\s*स्फुरद|\bस्फुरद\b)\b", re.IGNORECASE)),

    # Elemental / Reported Phosphorus [P]
    ("phosphorus", re.compile(r"\b(phosphorus(?:\s*\[P\]|\s*\(P\))?|\b\[P\]|\(P\)|\bP\s*\(available\)|\bP\s*level|\bP\s*content|\bP\s*value|\bP\s*ppm|\bP\s*kg\/ha)\b", re.IGNORECASE)),
    
    # Available Potassium (K2O / Avail K) - note K20 is OCR confusion
    ("available_potassium", re.compile(r"\b(available\s*potassium|avail(?:able|\.)?\s*k\b|k2o|k20|उपलब्ध\s*पालाश|\bपालाश\b)\b", re.IGNORECASE)),

    # Elemental / Reported Potassium [K]
    ("potassium", re.compile(r"\b(potassium(?:\s*\[K\]|\s*\(K\))?|\b\[K\]|\(K\)|\bK\s*\(available\)|\bK\s*level|\bK\s*content|\bK\s*value|\bK\s*ppm|\bK\s*kg\/ha)\b", re.IGNORECASE)),
    
    # Sulphur / Sulfur
    ("sulphur", re.compile(r"\b(sulphur|sulfur|avail(?:able|\.)?\s*s\b|available\s*sulphur|available\s*sulfur|\bs\b\s*\(available\)|\bso4\b|गंधक|सल्फर)", re.IGNORECASE)),
    
    # Zinc
    ("zinc", re.compile(r"\b(zinc|avail(?:able|\.)?\s*zn\b|available\s*zinc|\bzn\b|जस्त|झिंक)", re.IGNORECASE)),
    
    # Iron
    ("iron", re.compile(r"\b(iron|avail(?:able|\.)?\s*fe\b|available\s*iron|\bfe\b|लोह)", re.IGNORECASE)),
    
    # Manganese
    ("manganese", re.compile(r"\b(manganese|avail(?:able|\.)?\s*mn\b|available\s*manganese|\bmn\b|मॅंगनीज|मॅगनीज)", re.IGNORECASE)),
    
    # Copper
    ("copper", re.compile(r"\b(copper|avail(?:able|\.)?\s*cu\b|available\s*copper|\bcu\b|तांबे)", re.IGNORECASE)),
    
    # Boron
    ("boron", re.compile(r"\b(boron|avail(?:able|\.)?\s*b\b|available\s*boron|\[B\]|\(B\)|\bB\s*\(available\)|\bB\s*level|\bB\s*content|\bB\s*value|\bB\s*ppm|बोरॉन|बोरोन)\b", re.IGNORECASE)),
]

# Column definitions for horizontal/columnar multi-parameter tables
PARAMETER_COL_DEFS = [
    ("sample_col", re.compile(r"\b(sample(?:\s*no|\s*id|\s*#)?)\b", re.IGNORECASE)),
    ("soil_ph", re.compile(r"\b(p[hH](?:\s*\(1:2\.?5?\))?)\b(?!\.|\s*no\b|\s*num\b|\s*#|\s*:\s*\d{3,}|\s*-\s*\d{3,}|\s*\d{3,}|\s*os|\s*hate)", re.IGNORECASE)),
    ("available_phosphorus", re.compile(r"\b(available\s*phosphorus|avail(?:able|\.)?\s*p\b|p2o5|p205|उपलब्ध\s*स्फुरद)\b", re.IGNORECASE)),
    ("phosphorus", re.compile(r"\b(phosphorus(?:\s*\[P\]|\s*\(P\))?)\b", re.IGNORECASE)),
    ("available_potassium", re.compile(r"\b(available\s*potassium|avail(?:able|\.)?\s*k\b|k2o|k20|उपलब्ध\s*पालाश)\b", re.IGNORECASE)),
    ("potassium", re.compile(r"\b(potassium(?:\s*\[K\]|\s*\(K\))?)\b", re.IGNORECASE)),
    ("organic_matter", re.compile(r"\b(organic\s*matter|soil\s*organic\s*matter|s\.?o\.?m\.?\b|सेंद्रिय\s*पदार्थ)", re.IGNORECASE)),
    ("organic_carbon", re.compile(r"\b(organic\s*carbon|s\.?o\.?c\.?\b|o\.?c\.?\b|सेंद्रिय\s*कर्ब)", re.IGNORECASE)),
    ("available_nitrogen", re.compile(r"\b(available\s*nitrogen|avail(?:able|\.)?\s*n\b|उपलब्ध\s*नत्र)", re.IGNORECASE)),
    ("electrical_conductivity", re.compile(r"\b(electrical\s*conductivity|e\.?c\.?\b|conductivity|विद्युत\s*वाहकता)", re.IGNORECASE)),
    ("total_nitrogen", re.compile(r"\b(total\s*nitrogen|total\s*n\b|एकूण\s*नत्र)", re.IGNORECASE)),
    ("sulphur", re.compile(r"\b(sulphur|sulfur|avail(?:able|\.)?\s*s\b|गंधक)", re.IGNORECASE)),
    ("zinc", re.compile(r"\b(zinc|avail(?:able|\.)?\s*zn\b|जस्त)", re.IGNORECASE)),
    ("iron", re.compile(r"\b(iron|avail(?:able|\.)?\s*fe\b|लोह)", re.IGNORECASE)),
    ("manganese", re.compile(r"\b(manganese|avail(?:able|\.)?\s*mn\b|मॅंगनीज)", re.IGNORECASE)),
    ("copper", re.compile(r"\b(copper|avail(?:able|\.)?\s*cu\b|तांबे)", re.IGNORECASE)),
    ("boron", re.compile(r"\b(boron|avail(?:able|\.)?\s*b\b|बोरॉन)", re.IGNORECASE)),
]


class SoilReportParser:
    """
    Deterministic parser for structured text and Markdown tables extracted from soil reports.
    """

    def parse(
        self, text: str, pages: Optional[List[str]] = None
    ) -> Tuple[SoilReportMetadata, List[ExtractedSoilMeasurement]]:
        """
        Parses full report text stream into metadata and structured measurements.
        Supports multi-page documents and multi-sample reports.
        """
        if not text:
            return SoilReportMetadata(), []

        metadata = self._parse_metadata(text)

        if pages and len(pages) > 1:
            all_measurements = []
            for p_idx, page_text in enumerate(pages):
                page_measurements = self._parse_measurements(
                    page_text, page_num=p_idx + 1, default_depth=metadata.sample_depth
                )
                all_measurements.extend(page_measurements)
            measurements = self._deduplicate_measurements(all_measurements)
        else:
            measurements = self._parse_measurements(
                text, page_num=1, default_depth=metadata.sample_depth
            )

        return metadata, measurements

    def _parse_metadata(self, text: str) -> SoilReportMetadata:
        """
        Extract laboratory name, sample ID, dates, depth, and client location.
        """
        meta = SoilReportMetadata()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # 1. Laboratory Name
        lab_match = re.search(
            r"(?:Laboratory|Lab\s*Name|Testing\s*Laboratory|Testing\s*Lab|Samples\s*Analyzed\s*By|Analyzed\s*By)\b\s*[:=\-]\s*([^\n\r]+)",
            text,
            re.IGNORECASE,
        )
        if lab_match and lab_match.group(1).strip():
            meta.laboratory_name = lab_match.group(1).strip()
        else:
            # Check for header banner or line right after "Samples Analyzed By"
            found_banner = False
            for idx, line in enumerate(lines[:15]):
                if re.search(r"Samples\s*Analyzed\s*By|Analyzed\s*By", line, re.IGNORECASE):
                    if idx + 1 < len(lines):
                        meta.laboratory_name = lines[idx + 1].strip()
                        found_banner = True
                        break
            if not found_banner:
                for line in lines[:8]:
                    cleaned = line.lstrip("#* \t")
                    if any(
                        kw in cleaned.upper()
                        for kw in [
                            "SOIL TESTING LAB",
                            "KRISHI VIGYAN KENDRA",
                            "KVK",
                            "SOIL HEALTH CARD",
                            "AGRICULTURAL RESEARCH",
                            "AGRICULTURE DEPARTMENT",
                            "MPKV",
                            "ICAR",
                            "SOIL & PLANT ANALYSIS LAB",
                        ]
                    ):
                        meta.laboratory_name = cleaned.split("|")[0].strip()
                        break

        # 2. Sample ID and Lab Number
        lab_num_match = re.search(
            r"(?<![A-Za-z])(?:Lab\s*(?:Number|No|#))\s*[:=\-]?\s*([A-Za-z0-9\-_/]+)",
            text,
            re.IGNORECASE,
        )
        if lab_num_match:
            meta.lab_number = lab_num_match.group(1).strip()
            meta.sample_id = meta.lab_number

        sample_id_match = re.search(
            r"(?<![A-Za-z])(?:Sample\s*(?:ID|No|Number|Code|Ref|#))\s*[:=\-]?\s*([A-Za-z0-9\-_/]+)",
            text,
            re.IGNORECASE,
        )
        if sample_id_match:
            meta.sample_id = sample_id_match.group(1).strip()
            if not meta.lab_number:
                meta.lab_number = meta.sample_id

        # 3. Farmer / Client Name
        farmer_match = re.search(
            r"(?:Farmer(?:'s)?\s*Name|Customer\s*Name|Client\s*(?:Name)?|Grower\s*(?:Name)?)\s*[:=\-]?\s*([^\n\r,;|]+?)(?:,|\n|Date|Account|County|Send|$)",
            text,
            re.IGNORECASE,
        )
        if farmer_match:
            meta.farmer_name = farmer_match.group(1).strip()

        # Detect regional conventions (e.g. US date convention MM/DD/YYYY)
        is_us_doc = bool(re.search(r"\b(?:WI|Wisconsin|USA|County|lbs?|Extension)\b", text, re.IGNORECASE))

        # 4. Date Received (Stored distinctly from Collection Date!)
        recv_date_match = re.search(
            r"(?<![A-Za-z])(?:Date\s*received|Received\s*Date)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4})",
            text,
            re.IGNORECASE,
        )
        if recv_date_match:
            meta.date_received = self._normalize_date(recv_date_match.group(1).strip(), is_us=is_us_doc)

        # 5. Date Processed
        proc_date_match = re.search(
            r"(?<![A-Za-z])(?:Date\s*processed|Processed\s*Date)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4})",
            text,
            re.IGNORECASE,
        )
        if proc_date_match:
            meta.date_processed = self._normalize_date(proc_date_match.group(1).strip(), is_us=is_us_doc)

        # 6. Sample Collection Date (Strictly separate from Date Received - leaves null if not in document!)
        coll_date_match = re.search(
            r"(?<![A-Za-z])(?:Collection\s*Date|Date\s*of\s*Collection|Sampling\s*Date|Date\s*of\s*Sampling)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4})",
            text,
            re.IGNORECASE,
        )
        if coll_date_match:
            meta.collection_date = self._normalize_date(coll_date_match.group(1).strip(), is_us=is_us_doc)
        else:
            meta.collection_date = None

        # 7. Report Date (Issue date / date of report)
        report_date_match = re.search(
            r"(?<![A-Za-z])(?:Report\s*Date|Date\s*of\s*Report|Issue\s*Date|Date\s*of\s*Issue)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4})",
            text,
            re.IGNORECASE,
        )
        if report_date_match:
            meta.report_date = self._normalize_date(report_date_match.group(1).strip(), is_us=is_us_doc)
        elif meta.date_processed:
            meta.report_date = meta.date_processed

        # 8. Sample Depth & Provenance (Safeguard 6: preserve exact reported, do not guess)
        depth_match = re.search(
            r"(?:Sampling\s*Depth|Sample\s*Depth|Depth)\s*[:=\-]\s*([0-9]+\s*[-–to]\s*[0-9]+\s*(?:cm|in|inch|inches)?)",
            text,
            re.IGNORECASE,
        )
        if depth_match:
            meta.sample_depth = depth_match.group(1).strip()
            meta.depth_provenance = "LAB_REPORT"
        else:
            meta.sample_depth = None
            meta.depth_provenance = "UNKNOWN"

        # 7. Sampling Point
        point_match = re.search(
            r"(?:Sampling\s*Point|Plot\s*No|Survey\s*No|Gat\s*No|Field\s*ID)\s*[:=\-]\s*([^\n\r;|]+)",
            text,
            re.IGNORECASE,
        )
        if point_match:
            meta.sampling_point = point_match.group(1).strip()

        # 8. Geographic details
        village_match = re.search(r"\bVillage\s*[:=\-]\s*([A-Za-z\s]+?)(?:,|\n|$)", text, re.IGNORECASE)
        if village_match:
            meta.village = village_match.group(1).strip()

        taluka_match = re.search(r"\bTaluka\s*[:=\-]\s*([A-Za-z\s]+?)(?:,|\n|$)", text, re.IGNORECASE)
        if taluka_match:
            meta.taluka = taluka_match.group(1).strip()

        district_match = re.search(
            r"(?<![A-Za-z])(?:District|County)\b\s*[:=\-]\s*([A-Za-z\s]+?)(?:,|\n|Send|$)",
            text,
            re.IGNORECASE,
        )
        if district_match:
            meta.district = district_match.group(1).strip()

        state_match = re.search(r"\bState\s*[:=\-]\s*([A-Za-z\s]+?)(?:,|\n|$)", text, re.IGNORECASE)
        if state_match:
            meta.state = state_match.group(1).strip()

        return meta

    def _normalize_date(self, raw_date: str, is_us: bool = False) -> str:
        """
        Attempts to normalize date to YYYY-MM-DD format, or returns raw string.
        Supports international (%d/%m/%Y, %Y-%m-%d) and US (%m/%d/%Y) date formats.
        """
        formats_intl = [
            "%Y-%m-%d", "%Y/%m/%d",
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",
            "%d/%m/%y", "%d-%m-%y",
            "%m/%d/%y", "%m-%d-%y",
        ]
        formats_us = [
            "%Y-%m-%d", "%Y/%m/%d",
            "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%m/%d/%y", "%m-%d-%y",
            "%d/%m/%y", "%d-%m-%y",
        ]
        clean_date = raw_date.strip()
        parts = re.split(r"[/\-\.]", clean_date)
        if len(parts) == 3:
            try:
                p1, p2 = int(parts[0]), int(parts[1])
                if p1 > 12:
                    try_order = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"]
                elif p2 > 12:
                    try_order = ["%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", "%m/%d/%y", "%m-%d-%y"]
                else:
                    try_order = formats_us if is_us else formats_intl
            except ValueError:
                try_order = formats_us if is_us else formats_intl
        else:
            try_order = formats_us if is_us else formats_intl

        for fmt in try_order:
            try:
                dt = datetime.strptime(clean_date, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return raw_date

    def _parse_measurements(
        self, text: str, page_num: int = 1, default_depth: Optional[str] = None
    ) -> List[ExtractedSoilMeasurement]:
        """
        Extracts tabular or key-value parameter rows from text.
        Supports HTML tables (glm-ocr), Markdown tables, horizontal/columnar tables,
        whitespace vertical tables (pypdf), and key-value lines.
        """
        raw_measurements: List[ExtractedSoilMeasurement] = []

        # 1. HTML tables (from glm-ocr vision output)
        if "<table" in text.lower():
            html_m = self._parse_html_tables(text, page_num=page_num, default_depth=default_depth)
            raw_measurements.extend(html_m)

        # 2. Markdown pipe tables
        if "|" in text:
            table_measurements = self._parse_markdown_tables(text, page_num=page_num, default_depth=default_depth)
            raw_measurements.extend(table_measurements)

        # 3. Horizontal / Columnar whitespace tables (multi-sample tables e.g. lag_sample.pdf)
        col_measurements = self._parse_horizontal_columnar_tables(text, page_num=page_num, default_depth=default_depth)
        raw_measurements.extend(col_measurements)

        # 4. Space / tab-separated tabular rows (pypdf text streams, vertical format)
        ws_measurements = self._parse_whitespace_tables(text, page_num=page_num, default_depth=default_depth)
        raw_measurements.extend(ws_measurements)

        # 5. Key-value lines
        existing_keys = {m.parameter_key for m in raw_measurements}
        kv_measurements = self._parse_key_value_lines(
            text, exclude_keys=existing_keys, page_num=page_num, default_depth=default_depth
        )
        raw_measurements.extend(kv_measurements)

        return self._deduplicate_measurements(raw_measurements)

    def _deduplicate_measurements(
        self, measurements: List[ExtractedSoilMeasurement]
    ) -> List[ExtractedSoilMeasurement]:
        """
        Deduplicates measurements while strictly preserving multi-sample, multi-depth,
        and multi-page observations.
        """
        deduped: List[ExtractedSoilMeasurement] = []
        seen = set()
        for m in measurements:
            key = (m.parameter_key, m.sample_depth, m.sample_id, m.page_number)
            if key not in seen:
                seen.add(key)
                deduped.append(m)
        return deduped

    def _parse_horizontal_columnar_tables(
        self, text: str, page_num: int = 1, default_depth: Optional[str] = None
    ) -> List[ExtractedSoilMeasurement]:
        """
        Parses horizontal/columnar tables where column headers contain parameter names
        and rows contain sample observations (e.g. Sample pH Phosphorus Potassium Organic Matter).
        Excludes fertilizer recommendation sections and dosage tables.
        """
        measurements: List[ExtractedSoilMeasurement] = []
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # Contextual area designation and area type
        area_desig = None
        area_type = None
        for i, line in enumerate(lines):
            if re.search(r"Area\s*Designation", line, re.IGNORECASE):
                val = re.sub(r"^(?:Area\s*Designation\s*[:=\-]?\s*)+", "", line, flags=re.IGNORECASE).strip()
                if not val and i + 1 < len(lines):
                    val = lines[i + 1].strip()
                if val:
                    area_desig = val
            if re.search(r"Area\s*Type", line, re.IGNORECASE):
                val = re.sub(r"^(?:Area\s*Type\s*[:=\-]?\s*)+", "", line, flags=re.IGNORECASE).strip()
                if not val and i + 1 < len(lines):
                    val = lines[i + 1].strip()
                if val:
                    area_type = val

        in_recommendations = False

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect recommendation or dosage sections (e.g. "RECOMMENDATIONS", "Fertilizer to Apply", "खत शिफारशी")
            if re.search(r"\b(?:RECOMMENDATIONS|Fertilizer to Apply|Actual Nutrient Need|Lime to Apply|खत\s*शिफारशी|खतांची\s*मात्रा|शिफारशी|खतांचा\s*डोस|Recommended\s*Dose|RDF)\b", line, re.IGNORECASE):
                in_recommendations = True
            elif re.search(r"\b(?:LABORATORY ANALYSIS|SOIL TEST RESULTS|TEST RESULTS|ANALYTICAL REPORT|माती\s*परीक्षण\s*निकाल)\b", line, re.IGNORECASE):
                in_recommendations = False

            # Explicit guardrail: Skip recommendation sections and dosage headers
            if in_recommendations:
                i += 1
                continue

            # Skip lines containing fertilizer dosage rate units (e.g. lbs/100 ft², lbs/1000 ft², lbs/acre, kg/ha recommended, किलो/एकर)
            if re.search(r"\b(?:lbs?/(?:100|1,?000)?\s*ft|lbs?/acre|kg/ha\s*recommended|किलो/एकर|किलो/हेक्टर|पिशव्या/एकर)\b", line, re.IGNORECASE):
                i += 1
                continue

            if re.match(r"^\s*\d+\s+", line):
                i += 1
                continue

            # Check if line looks like a columnar table header with 2 or more parameter columns
            col_matches = []
            for key, pat in PARAMETER_COL_DEFS:
                for m in pat.finditer(line):
                    col_matches.append((m.start(), m.end(), key, m.group(0)))

            distinct_params = {key for _, _, key, _ in col_matches if key != "sample_col"}
            if len(distinct_params) >= 2 and len(line) < 120 and not re.search(r"\b(?:will|should|apply|increase|decrease|because|between|during)\b", line, re.IGNORECASE):
                col_matches.sort(key=lambda x: x[0])
                # Deduplicate overlapping matches
                filtered_matches = []
                last_end = -1
                for m_start, m_end, m_key, m_text in col_matches:
                    if m_start >= last_end:
                        filtered_matches.append((m_start, m_end, m_key, m_text))
                        last_end = m_end

                columns = []
                for c_idx, (start, end, key, text_match) in enumerate(filtered_matches):
                    next_start = filtered_matches[c_idx + 1][0] if c_idx + 1 < len(filtered_matches) else len(line)
                    col_header = line[start:next_start].strip()

                    # Extract unit from header
                    unit = None
                    unit_m = re.search(r"\(([^)]+)\)|(\b(?:ppm|mg/kg|kg/ha|g/kg|dS/m)\b)|(%)", col_header, re.IGNORECASE)
                    if unit_m:
                        unit = unit_m.group(1) or unit_m.group(2) or unit_m.group(3)
                    elif key == "soil_ph":
                        unit = "pH"

                    columns.append({
                        "key": key,
                        "header": col_header,
                        "unit": unit,
                    })

                # Scan subsequent lines for data row(s)
                r_idx = i + 1
                while r_idx < len(lines):
                    row_line = lines[r_idx]
                    # Terminate table scanning if new section or document footer
                    if re.search(r"\b(?:RECOMMENDATIONS|WEB COPY|Page \d+|LABORATORY ANALYSIS)\b", row_line, re.IGNORECASE):
                        break

                    tokens = row_line.split()
                    num_tokens = [t for t in tokens if re.match(r"^[<>]?\s*[-+]?\d+(?:\.\d+)?$", t)]

                    # If row has numbers corresponding to the parameter columns
                    if len(num_tokens) >= len(columns) - 1:
                        sample_id = None
                        val_idx = 0
                        for col in columns:
                            if col["key"] == "sample_col":
                                if val_idx < len(tokens):
                                    sample_id = tokens[val_idx]
                                    val_idx += 1
                                continue
                            if val_idx < len(tokens):
                                val_str = tokens[val_idx]
                                parsed_val, is_reported, is_amb, amb_reason = self._parse_numeric_value(val_str)
                                if is_reported and parsed_val is not None:
                                    meas = ExtractedSoilMeasurement(
                                        parameter_key=col["key"],
                                        original_parameter_name=col["header"],
                                        original_value=parsed_val,
                                        original_unit=col["unit"],
                                        sample_id=sample_id,
                                        sample_designation=area_desig,
                                        area_type=area_type,
                                        page_number=page_num,
                                        sample_depth=default_depth,
                                        ocr_confidence=0.85 if is_amb else 1.0,
                                        is_ambiguous=is_amb,
                                        ambiguity_reason=amb_reason,
                                        extraction_status=ParameterExtractionStatus.EXTRACTED.value,
                                        verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
                                    )
                                    measurements.append(meas)
                                val_idx += 1
                        r_idx += 1
                    else:
                        break
            i += 1

        return measurements

    def _parse_html_tables(
        self, text: str, page_num: int = 1, default_depth: Optional[str] = None
    ) -> List[ExtractedSoilMeasurement]:
        """
        Parses HTML formatted tables (as produced by glm-ocr vision models).
        """
        measurements: List[ExtractedSoilMeasurement] = []
        table_blocks = re.findall(r"<table[^>]*>(.*?)</table>", text, re.IGNORECASE | re.DOTALL)
        for t_content in table_blocks:
            row_matches = re.findall(r"<tr[^>]*>(.*?)</tr>", t_content, re.IGNORECASE | re.DOTALL)
            if not row_matches:
                continue

            # First row: headers
            header_cells = re.findall(r"<th[^>]*>(.*?)</th>", row_matches[0], re.IGNORECASE | re.DOTALL)
            start_row = 1
            if not header_cells:
                td_first = re.findall(r"<td[^>]*>(.*?)</td>", row_matches[0], re.IGNORECASE | re.DOTALL)
                clean_td_first = [re.sub(r"<[^>]+>", "", c).strip() for c in td_first]
                if any(k in " ".join(clean_td_first).lower() for k in ["param", "test", "result", "unit", "value", "nutrient"]):
                    header_cells = clean_td_first
                else:
                    header_cells = [f"Col {idx}" for idx in range(len(clean_td_first))]
                    start_row = 0
            else:
                header_cells = [re.sub(r"<[^>]+>", "", c).strip() for c in header_cells]

            col_map = self._classify_table_columns(header_cells)
            for r_html in row_matches[start_row:]:
                td_cells = [
                    re.sub(r"<[^>]+>", "", c).strip()
                    for c in re.findall(r"<(?:td|th)[^>]*>(.*?)<\/(?:td|th)>", r_html, re.IGNORECASE | re.DOTALL)
                ]
                if td_cells:
                    row_m = self._parse_table_row(td_cells, col_map, header_cells, page_num=page_num, default_depth=default_depth)
                    measurements.extend(row_m)

        return measurements

    def _parse_whitespace_tables(
        self, text: str, page_num: int = 1, default_depth: Optional[str] = None
    ) -> List[ExtractedSoilMeasurement]:
        """
        Parses space/tab-separated tabular rows (as produced by pypdf digital text extraction).
        Handles multi-depth columns (e.g. 0-15 cm, 15-30 cm) and single-value rows.
        """
        measurements: List[ExtractedSoilMeasurement] = []
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # Check for multi-depth header line
        depth_columns: List[str] = []
        for line in lines:
            d_matches = re.findall(r"(\d+\s*[-–to]\s*\d+\s*(?:cm|in)?)", line, re.IGNORECASE)
            if len(d_matches) >= 2 and any(k in line.lower() for k in ["param", "depth", "test"]):
                depth_columns = d_matches
                break

        unit_regex = re.compile(
            r"(?:\b(?:pH|dS/m|mS/cm|mmhos/cm|uS/cm|kg/ha|kg/acre|ppm|mg/kg|g/kg)\b|%)",
            re.IGNORECASE
        )

        in_rec_section = False
        for line in lines:
            line_str = line.strip()
            line_lower = line_str.lower()

            # Safeguard: Do not extract fertilizer recommendation table numbers as soil measurements
            if any(h in line_lower for h in [
                "recommendations", "fertilizer to apply", "nutrient need", "lime to apply",
                "खत शिफारशी", "खतांची मात्रा", "शिफारशी", "खतांचा डोस", "fertilizer recommendations",
                "dose of fertilizer", "rdf", "युरिया", "रासायनिक खते"
            ]):
                in_rec_section = True
            if any(h in line_lower for h in ["laboratory analysis", "soil test results", "analytical results", "test parameters", "माती परीक्षण निकाल"]):
                in_rec_section = False

            if in_rec_section and not any(h in line_lower for h in ["laboratory analysis", "soil test results", "माती परीक्षण निकाल"]):
                continue

            if line.startswith("|") or "<td" in line.lower() or "<table" in line.lower():
                continue

            cleaned = re.sub(r"^\s*\d+\s+", "", line)
            # Mask dilution ratios like 1:2.5 or 1:2
            masked = re.sub(r"\d+:\d+(?:\.\d+)?", "ratio", cleaned)

            param_key, ocr_artifact, ambiguity_note = self._identify_parameter(cleaned)
            if not param_key:
                continue

            # Check if unmeasured / missing
            if any(t in cleaned.lower() for t in ["nil", "n/a", "not tested", "unmeasured", "not done"]):
                m = ExtractedSoilMeasurement(
                    parameter_key=param_key,
                    original_parameter_name=cleaned,
                    original_value=None,
                    original_unit=None,
                    sample_depth=default_depth,
                    page_number=page_num,
                    extraction_status=ParameterExtractionStatus.NOT_REPORTED.value,
                    verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
                )
                measurements.append(m)
                continue

            # Extract unit
            um = unit_regex.search(line)
            raw_unit = um.group(0) if um else None

            # Extract numbers (before the unit if possible to avoid catching percentage in method)
            masked_for_nums = masked
            if um:
                unit_pos = masked.lower().find(um.group(0).lower())
                if unit_pos != -1:
                    masked_before_unit = masked[:unit_pos]
                    nums_before = re.findall(r"(?<![A-Za-z\-_/])(?:[<>]?\s*[-+]?\d+(?:\.\d+)?|\d+\.\d+)(?![A-Za-z\-_/])", masked_before_unit)
                    if nums_before:
                        num_matches = nums_before
                    else:
                        num_matches = re.findall(r"(?<![A-Za-z\-_/])(?:[<>]?\s*[-+]?\d+(?:\.\d+)?|\d+\.\d+)(?![A-Za-z\-_/])", masked)
                else:
                    num_matches = re.findall(r"(?<![A-Za-z\-_/])(?:[<>]?\s*[-+]?\d+(?:\.\d+)?|\d+\.\d+)(?![A-Za-z\-_/])", masked)
            else:
                num_matches = re.findall(r"(?<![A-Za-z\-_/])(?:[<>]?\s*[-+]?\d+(?:\.\d+)?|\d+\.\d+)(?![A-Za-z\-_/])", masked)

            if not num_matches:
                continue

            # Multi-depth row
            if len(depth_columns) >= 2 and len(num_matches) >= 2:
                for idx, depth_str in enumerate(depth_columns[:len(num_matches)]):
                    parsed_val, is_rep, is_amb, val_amb_reason = self._parse_numeric_value(num_matches[idx])
                    is_ambiguous = ocr_artifact or is_amb
                    reasons = [r for r in [ambiguity_note, val_amb_reason] if r]
                    m = ExtractedSoilMeasurement(
                        parameter_key=param_key,
                        original_parameter_name=cleaned,
                        original_value=parsed_val,
                        original_unit=raw_unit,
                        sample_depth=depth_str,
                        page_number=page_num,
                        ocr_confidence=0.80 if is_ambiguous else 1.0,
                        is_ambiguous=is_ambiguous,
                        ambiguity_reason="; ".join(reasons) if reasons else None,
                        extraction_status=ParameterExtractionStatus.EXTRACTED.value if is_rep else ParameterExtractionStatus.NOT_REPORTED.value,
                        verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
                    )
                    measurements.append(m)
            else:
                # Single value row
                parsed_val, is_rep, is_amb, val_amb_reason = self._parse_numeric_value(num_matches[0])
                is_ambiguous = ocr_artifact or is_amb
                reasons = [r for r in [ambiguity_note, val_amb_reason] if r]
                m = ExtractedSoilMeasurement(
                    parameter_key=param_key,
                    original_parameter_name=cleaned,
                    original_value=parsed_val,
                    original_unit=raw_unit,
                    sample_depth=default_depth,
                    page_number=page_num,
                    ocr_confidence=0.80 if is_ambiguous else 1.0,
                    is_ambiguous=is_ambiguous,
                    ambiguity_reason="; ".join(reasons) if reasons else None,
                    extraction_status=ParameterExtractionStatus.EXTRACTED.value if is_rep else ParameterExtractionStatus.NOT_REPORTED.value,
                    verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
                )
                measurements.append(m)

        return measurements

    def _parse_markdown_tables(
        self, text: str, page_num: int = 1, default_depth: Optional[str] = None
    ) -> List[ExtractedSoilMeasurement]:
        """
        Parses Markdown formatted tables with header classification.
        """
        measurements: List[ExtractedSoilMeasurement] = []
        lines = text.splitlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("|") and line.endswith("|"):
                header_line = line
                if i + 1 < len(lines) and re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", lines[i + 1].strip()):
                    headers = [c.strip() for c in header_line.split("|")[1:-1]]
                    col_map = self._classify_table_columns(headers)
                    i += 2  # Skip header and separator

                    while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                        row_line = lines[i].strip()
                        cells = [c.strip() for c in row_line.split("|")[1:-1]]
                        row_measurements = self._parse_table_row(
                            cells, col_map, headers, page_num=page_num, default_depth=default_depth
                        )
                        measurements.extend(row_measurements)
                        i += 1
                    continue
            i += 1

        return measurements

    def _classify_table_columns(self, headers: List[str]) -> Dict[str, Any]:
        """
        Identifies semantic roles of table columns from header text.
        """
        col_map: Dict[str, Any] = {
            "param_idx": -1,
            "value_indices": [],  # list of (col_idx, depth_label)
            "unit_idx": -1,
            "rating_idx": -1,
            "method_idx": -1,
            "range_idx": -1,
        }

        for idx, h in enumerate(headers):
            h_lower = h.lower()
            # Depth check in header (e.g. "0-15 cm", "Result (0-15cm)")
            depth_in_col = re.search(r"(\d+\s*[-–to]\s*\d+\s*(?:cm|in)?)", h_lower)

            if any(k in h_lower for k in ["param", "test", "nutrient", "element", "property", "घटक"]):
                col_map["param_idx"] = idx
            elif any(k in h_lower for k in ["unit", "एकक"]):
                col_map["unit_idx"] = idx
            elif any(k in h_lower for k in ["rating", "status", "category", "interpretation", "श्रेणी"]):
                col_map["rating_idx"] = idx
            elif any(k in h_lower for k in ["method", "procedure", "पद्धत"]):
                col_map["method_idx"] = idx
            elif any(k in h_lower for k in ["range", "critical", "reference", "मर्यादा"]):
                col_map["range_idx"] = idx
            elif any(k in h_lower for k in ["result", "value", "reading", "obs", "निष्कर्ष", "प्रमाण"]) or depth_in_col:
                col_map["value_indices"].append((idx, depth_in_col.group(1) if depth_in_col else None))

        # Default fallbacks if standard keywords were abbreviated
        if col_map["param_idx"] == -1 and len(headers) >= 2:
            # Often col 0 is Sr. No. and col 1 is Parameter
            col_map["param_idx"] = 1 if len(headers) > 2 else 0

        if not col_map["value_indices"] and len(headers) >= 3:
            # Often col 2 is Value
            col_map["value_indices"].append((2, None))

        if col_map["unit_idx"] == -1 and len(headers) >= 4:
            col_map["unit_idx"] = 3

        return col_map

    def _parse_table_row(
        self,
        cells: List[str],
        col_map: Dict[str, Any],
        headers: List[str],
        page_num: int = 1,
        default_depth: Optional[str] = None,
    ) -> List[ExtractedSoilMeasurement]:
        """
        Parses a single row of cells into one or more ExtractedSoilMeasurement objects.
        """
        p_idx = col_map["param_idx"]
        if p_idx < 0 or p_idx >= len(cells):
            return []

        raw_param_name = cells[p_idx].strip()
        if not raw_param_name:
            return []

        # Identify canonical parameter
        param_key, ocr_artifact_flag, ambiguity_note = self._identify_parameter(raw_param_name)
        if not param_key:
            return []

        # Extract unit if column present
        u_idx = col_map["unit_idx"]
        raw_unit = cells[u_idx].strip() if 0 <= u_idx < len(cells) else None

        # Extract rating
        r_idx = col_map["rating_idx"]
        rating = cells[r_idx].strip() if 0 <= r_idx < len(cells) else None

        # Extract method
        m_idx = col_map["method_idx"]
        method = cells[m_idx].strip() if 0 <= m_idx < len(cells) else None

        # Extract range
        range_idx = col_map["range_idx"]
        ref_range = cells[range_idx].strip() if 0 <= range_idx < len(cells) else None

        results = []
        for val_idx, col_depth in col_map["value_indices"]:
            if val_idx >= len(cells):
                continue
            raw_val_str = cells[val_idx].strip()
            parsed_val, is_reported, is_val_ambiguous, val_ambiguity_reason = self._parse_numeric_value(raw_val_str)

            # Determine depth
            eff_depth = col_depth or default_depth

            is_ambiguous = ocr_artifact_flag or is_val_ambiguous
            ambiguity_reasons = []
            if ambiguity_note:
                ambiguity_reasons.append(ambiguity_note)
            if val_ambiguity_reason:
                ambiguity_reasons.append(val_ambiguity_reason)

            measurement = ExtractedSoilMeasurement(
                parameter_key=param_key,
                original_parameter_name=raw_param_name,
                original_value=parsed_val,
                original_unit=raw_unit,
                sample_depth=eff_depth,
                analytical_method=method,
                laboratory_rating=rating,
                reference_range=ref_range,
                page_number=page_num,
                ocr_confidence=0.80 if is_ambiguous else 1.0,
                is_ambiguous=is_ambiguous,
                ambiguity_reason="; ".join(ambiguity_reasons) if ambiguity_reasons else None,
                extraction_status=(
                    ParameterExtractionStatus.EXTRACTED.value
                    if is_reported
                    else ParameterExtractionStatus.NOT_REPORTED.value
                ),
                verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
            )
            results.append(measurement)

        return results

    def _parse_key_value_lines(
        self,
        text: str,
        exclude_keys: set,
        page_num: int = 1,
        default_depth: Optional[str] = None,
    ) -> List[ExtractedSoilMeasurement]:
        """
        Parses non-tabular key-value lines like 'Available Nitrogen: 195 kg/ha'.
        """
        measurements: List[ExtractedSoilMeasurement] = []
        lines = text.splitlines()

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("|"):
                continue

            # Look for colon, equal, or dash delimiter
            match = re.match(
                r"^[-*#\s\d\.]*([A-Za-z\(\)\s\d\/\.%\-_]+?)\s*[:=\-]\s*([<>]?\s*[\d\.,OIl\?\*]+(?:\s*[A-Za-z/%]+)?.*)$",
                line_str,
            )
            if not match:
                continue

            param_text = match.group(1).strip()
            rest_text = match.group(2).strip()

            param_key, ocr_artifact_flag, ambiguity_note = self._identify_parameter(param_text)
            if not param_key or param_key in exclude_keys:
                continue

            # Extract numeric value and potential unit from rest_text
            val_match = re.search(r"([<>]?\s*[\d\.,OIl\?\*]+)", rest_text)
            if not val_match:
                continue

            raw_val_str = val_match.group(1).strip()
            parsed_val, is_reported, is_val_ambiguous, val_ambiguity_reason = self._parse_numeric_value(raw_val_str)

            # Try to grab unit after number
            unit_remainder = rest_text[val_match.end():].strip()
            unit_match = re.match(r"^([a-zA-Z/%]+(?:\s*/\s*[a-zA-Z]+)?)", unit_remainder)
            raw_unit = unit_match.group(1).strip() if unit_match else None

            is_ambiguous = ocr_artifact_flag or is_val_ambiguous
            ambiguity_reasons = []
            if ambiguity_note:
                ambiguity_reasons.append(ambiguity_note)
            if val_ambiguity_reason:
                ambiguity_reasons.append(val_ambiguity_reason)

            m = ExtractedSoilMeasurement(
                parameter_key=param_key,
                original_parameter_name=param_text,
                original_value=parsed_val,
                original_unit=raw_unit,
                sample_depth=default_depth,
                page_number=page_num,
                ocr_confidence=0.80 if is_ambiguous else 1.0,
                is_ambiguous=is_ambiguous,
                ambiguity_reason="; ".join(ambiguity_reasons) if ambiguity_reasons else None,
                extraction_status=(
                    ParameterExtractionStatus.EXTRACTED.value
                    if is_reported
                    else ParameterExtractionStatus.NOT_REPORTED.value
                ),
                verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
            )
            measurements.append(m)
            exclude_keys.add(param_key)

        return measurements

    def _identify_parameter(self, text: str) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Matches a raw parameter string to canonical key.
        Detects known OCR confusions (e.g. P206 for P2O5, K20 for K2O).
        Returns: (canonical_key, is_ambiguous_artifact, ambiguity_reason)
        """
        clean_text = text.strip()
        t_lower = clean_text.lower()

        # Check for known OCR confusions first
        if "p206" in t_lower or "p205" in t_lower:
            return "available_phosphorus", True, "OCR digit confusion detected: P206/P205 for P2O5"
        if "k20" in t_lower:
            return "available_potassium", True, "OCR digit confusion detected: K20 for K2O"
        if "s04" in t_lower:
            return "sulphur", True, "OCR digit confusion detected: S04 for SO4"

        for canon_key, pattern in PARAMETER_PATTERNS:
            if pattern.search(clean_text):
                # Ensure Total Nitrogen is not classified as Available Nitrogen
                if canon_key == "available_nitrogen" and re.search(r"\btotal\b", t_lower):
                    continue
                # Ensure Organic Matter is not classified as Organic Carbon
                if canon_key == "organic_carbon" and re.search(r"\bmatter\b", t_lower):
                    continue
                # Ensure elemental Phosphorus is not classified as Available Phosphorus
                if canon_key == "available_phosphorus" and not re.search(r"\b(?:available|avail|p2o5|p205|p206|p2o|उपलब्ध)\b", t_lower):
                    continue
                # Ensure elemental Potassium is not classified as Available Potassium
                if canon_key == "available_potassium" and not re.search(r"\b(?:available|avail|k2o|k20|उपलब्ध)\b", t_lower):
                    continue
                return canon_key, False, None

        return None, False, None

    def _parse_numeric_value(
        self, raw_str: str
    ) -> Tuple[Optional[float], bool, bool, Optional[str]]:
        """
        Parses a numeric string.
        Safeguard 1: Missing/unmeasured returns (None, False, False, None).
        Safeguard 7: Ambiguous characters return (parsed_val, is_reported, True, reason).
        """
        if not raw_str:
            return None, False, False, None

        s = raw_str.strip()

        # Check for unmeasured / missing tokens
        missing_tokens = ["-", "--", "---", "nil", "na", "n/a", "nd", "bdl", "not tested", "unmeasured", "not done"]
        if s.lower() in missing_tokens or s == "":
            return None, False, False, None

        is_ambiguous = False
        ambiguity_reason = None

        # Check for blur/glare indicators or explicit questions
        if any(marker in s for marker in ["?", "*", "glare", "blur", "smudge"]):
            is_ambiguous = True
            ambiguity_reason = f"Optical degradation or marker detected in reading: '{s}'"
            s = re.sub(r"[\?\*]|glare|blur|smudge", "", s).strip()

        # Check for OCR character substitutions in numbers (e.g. O for 0, l for 1)
        sub_made = False
        if re.search(r"\d+[OIl]\d*", s) or re.search(r"[OIl]\.\d+", s):
            orig_s = s
            s = s.replace("O", "0").replace("o", "0").replace("l", "1").replace("I", "1")
            is_ambiguous = True
            sub_made = True
            ambiguity_reason = f"OCR character substitution detected ('{orig_s}' -> '{s}')"

        # Remove comparator symbols (<, >, ~, ±) but record presence
        if s.startswith(("<", ">", "~", "±")):
            sym = s[0]
            s = s[1:].strip()
            if not is_ambiguous:
                is_ambiguous = True
                ambiguity_reason = f"Threshold/approximate symbol '{sym}' detected in reading"

        # Extract standard float
        match = re.search(r"[-+]?\d*\.?\d+", s)
        if match:
            try:
                val = float(match.group(0))
                return val, True, is_ambiguous, ambiguity_reason
            except ValueError:
                pass

        # If we reach here, unparseable string
        return None, False, True, f"Unparseable numeric value: '{raw_str}'"
