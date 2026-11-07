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
    ("available_nitrogen", re.compile(r"\b(available\s*nitrogen|avail(?:able|\.)?\s*n\b|mineral\s*nitrogen|उपलब्ध\s*नत्र)", re.IGNORECASE)),
    
    # Organic Matter (SOM) (checked before OC to prevent SOM matching OC)
    ("organic_matter", re.compile(r"\b(organic\s*matter|soil\s*organic\s*matter|s\.?o\.?m\.?\b|सेंद्रिय\s*पदार्थ)", re.IGNORECASE)),
    
    # Organic Carbon (SOC)
    ("organic_carbon", re.compile(r"\b(organic\s*carbon|s\.?o\.?c\.?\b|o\.?c\.?\b|सेंद्रिय\s*कर्ब)", re.IGNORECASE)),
    
    # Soil pH (exclude Phosphorus matches)
    ("soil_ph", re.compile(r"(?:\bsoil\s*p[hH]\b|\bp[hH]\b(?!\s*osphorus|\s*os\b|\s*hate)|\bp[hH]\s*\(1:2\.?5?\)|\bसामू\b)", re.IGNORECASE)),
    
    # Electrical Conductivity (EC)
    ("electrical_conductivity", re.compile(r"\b(electrical\s*conductivity|e\.?c\.?\b|conductivity|विद्युत\s*वाहकता)", re.IGNORECASE)),
    
    # Available Phosphorus (P2O5 / P) - note P206 is OCR confusion
    ("available_phosphorus", re.compile(r"\b(available\s*phosphorus|avail(?:able|\.)?\s*p\b|p2o5|p205|p206|p2o|उपलब्ध\s*स्फुरद)", re.IGNORECASE)),
    
    # Available Potassium (K2O / K) - note K20 is OCR confusion
    ("available_potassium", re.compile(r"\b(available\s*potassium|avail(?:able|\.)?\s*k\b|k2o|k20|उपलब्ध\s*पालाश)", re.IGNORECASE)),
    
    # Sulphur / Sulfur
    ("sulphur", re.compile(r"\b(sulphur|sulfur|avail(?:able|\.)?\s*s\b|available\s*sulphur|available\s*sulfur|\bs\b\s*\(available\)|\bso4\b|गंधक)", re.IGNORECASE)),
    
    # Zinc
    ("zinc", re.compile(r"\b(zinc|avail(?:able|\.)?\s*zn\b|available\s*zinc|\bzn\b|जस्त)", re.IGNORECASE)),
    
    # Iron
    ("iron", re.compile(r"\b(iron|avail(?:able|\.)?\s*fe\b|available\s*iron|\bfe\b|लोह)", re.IGNORECASE)),
    
    # Manganese
    ("manganese", re.compile(r"\b(manganese|avail(?:able|\.)?\s*mn\b|available\s*manganese|\bmn\b|मॅंगनीज)", re.IGNORECASE)),
    
    # Copper
    ("copper", re.compile(r"\b(copper|avail(?:able|\.)?\s*cu\b|available\s*copper|\bcu\b|तांबे)", re.IGNORECASE)),
    
    # Boron
    ("boron", re.compile(r"\b(boron|avail(?:able|\.)?\s*b\b|available\s*boron|\bb\b(?!\s*arcode)|बोरॉन)", re.IGNORECASE)),
]


class SoilReportParser:
    """
    Deterministic parser for structured text and Markdown tables extracted from soil reports.
    """

    def parse(self, text: str) -> Tuple[SoilReportMetadata, List[ExtractedSoilMeasurement]]:
        """
        Parses full report text stream into metadata and structured measurements.
        """
        if not text:
            return SoilReportMetadata(), []

        metadata = self._parse_metadata(text)
        measurements = self._parse_measurements(text, default_depth=metadata.sample_depth)

        return metadata, measurements

    def _parse_metadata(self, text: str) -> SoilReportMetadata:
        """
        Extract laboratory name, sample ID, dates, depth, and client location.
        """
        meta = SoilReportMetadata()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # 1. Laboratory Name
        lab_match = re.search(
            r"(?:Laboratory|Lab Name|Testing Lab|Testing Laboratory)\s*[:=\-]\s*([^\n\r]+)",
            text,
            re.IGNORECASE,
        )
        if lab_match:
            meta.laboratory_name = lab_match.group(1).strip()
        else:
            # Check for header banner lab name in the first 8 lines
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
                    ]
                ):
                    meta.laboratory_name = cleaned.split("|")[0].strip()
                    break

        # 2. Sample ID
        sample_id_match = re.search(
            r"(?:Sample\s*(?:ID|No|Number|Code|Ref)|Lab\s*Sample\s*No)\s*[:=\-]\s*([A-Za-z0-9\-_/]+)",
            text,
            re.IGNORECASE,
        )
        if sample_id_match:
            meta.sample_id = sample_id_match.group(1).strip()

        # 3. Farmer Name
        farmer_match = re.search(
            r"(?:Farmer(?:'s)?\s*Name|Customer\s*Name)\s*[:=\-]\s*([^\n\r,;|]+)",
            text,
            re.IGNORECASE,
        )
        if farmer_match:
            meta.farmer_name = farmer_match.group(1).strip()

        # 4. Report Date
        report_date_match = re.search(
            r"(?:Report\s*Date|Date\s*of\s*Report|Issue\s*Date|Date\s*of\s*Issue)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4})",
            text,
            re.IGNORECASE,
        )
        if report_date_match:
            meta.report_date = self._normalize_date(report_date_match.group(1).strip())

        # 5. Collection Date
        coll_date_match = re.search(
            r"(?:Collection\s*Date|Date\s*of\s*Collection|Sampling\s*Date|Date\s*of\s*Sampling)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4})",
            text,
            re.IGNORECASE,
        )
        if coll_date_match:
            meta.collection_date = self._normalize_date(coll_date_match.group(1).strip())

        # 6. Sample Depth (Safeguard 6: preserve exact reported, do not guess)
        depth_match = re.search(
            r"(?:Sampling\s*Depth|Sample\s*Depth|Depth)\s*[:=\-]\s*([0-9]+\s*[-–to]\s*[0-9]+\s*(?:cm|in|inch|inches)?)",
            text,
            re.IGNORECASE,
        )
        if depth_match:
            meta.sample_depth = depth_match.group(1).strip()

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

        district_match = re.search(r"\bDistrict\s*[:=\-]\s*([A-Za-z\s]+?)(?:,|\n|$)", text, re.IGNORECASE)
        if district_match:
            meta.district = district_match.group(1).strip()

        state_match = re.search(r"\bState\s*[:=\-]\s*([A-Za-z\s]+?)(?:,|\n|$)", text, re.IGNORECASE)
        if state_match:
            meta.state = state_match.group(1).strip()

        return meta

    def _normalize_date(self, raw_date: str) -> str:
        """
        Attempts to normalize date to YYYY-MM-DD format, or returns raw string.
        """
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%Y-%m-%d", "%Y/%m/%d",
            "%d/%m/%y", "%d-%m-%y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(raw_date, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return raw_date

    def _parse_measurements(
        self, text: str, default_depth: Optional[str] = None
    ) -> List[ExtractedSoilMeasurement]:
        """
        Extracts tabular or key-value parameter rows from text.
        Supports HTML tables (glm-ocr), Markdown tables, and whitespace tables (pypdf).
        """
        raw_measurements: List[ExtractedSoilMeasurement] = []

        # 1. HTML tables (from glm-ocr vision output)
        if "<table" in text.lower():
            html_m = self._parse_html_tables(text, default_depth=default_depth)
            raw_measurements.extend(html_m)

        # 2. Markdown pipe tables
        if "|" in text:
            table_measurements = self._parse_markdown_tables(text, default_depth=default_depth)
            raw_measurements.extend(table_measurements)

        # 3. Space / tab-separated tabular rows (pypdf text streams)
        ws_measurements = self._parse_whitespace_tables(text, default_depth=default_depth)
        raw_measurements.extend(ws_measurements)

        # 4. Key-value lines
        existing_keys = {m.parameter_key for m in raw_measurements}
        kv_measurements = self._parse_key_value_lines(
            text, exclude_keys=existing_keys, default_depth=default_depth
        )
        raw_measurements.extend(kv_measurements)

        # De-duplicate while preserving multi-depth variations
        deduped: List[ExtractedSoilMeasurement] = []
        seen = set()
        for m in raw_measurements:
            pair = (m.parameter_key, m.sample_depth)
            if pair not in seen:
                seen.add(pair)
                deduped.append(m)

        return deduped

    def _parse_html_tables(
        self, text: str, default_depth: Optional[str] = None
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
                    row_m = self._parse_table_row(td_cells, col_map, header_cells, default_depth=default_depth)
                    measurements.extend(row_m)

        return measurements

    def _parse_whitespace_tables(
        self, text: str, default_depth: Optional[str] = None
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

        for line in lines:
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
                    ocr_confidence=0.80 if is_ambiguous else 1.0,
                    is_ambiguous=is_ambiguous,
                    ambiguity_reason="; ".join(reasons) if reasons else None,
                    extraction_status=ParameterExtractionStatus.EXTRACTED.value if is_rep else ParameterExtractionStatus.NOT_REPORTED.value,
                    verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
                )
                measurements.append(m)

        return measurements

    def _parse_markdown_tables(
        self, text: str, default_depth: Optional[str] = None
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
                            cells, col_map, headers, default_depth=default_depth
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
