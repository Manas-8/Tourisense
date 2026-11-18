"""Read-only tourism data services. The source workbook has no year column."""
import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "Data"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _xlsx_rows(path):
    """Read the simple shared-string first-sheet workbook without extra dependencies."""
    with zipfile.ZipFile(path) as archive:
        shared = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        strings = ["".join(t.text or "" for t in item.iter("{%s}t" % NS["m"])) for item in shared]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall(".//m:sheetData/m:row", NS):
            values = []
            for cell in row.findall("m:c", NS):
                value = cell.find("m:v", NS)
                text = value.text if value is not None else ""
                if cell.get("t") == "s" and text:
                    text = strings[int(text)]
                values.append(text)
            rows.append(values)
    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[1:] if any(row)]


def _tourism_rows():
    rows = _xlsx_rows(DATA / "user_visits.xlsx")
    out = []
    for row in rows:
        try:
            out.append({
                "month": row["Month"].strip(), "state": row["State"].strip(),
                "domestic_tourists": int(row["Domestic Tourists"]),
                "foreign_tourists": int(row["Foreign Tourists"]),
                "total_tourists": int(row["Total Tourists"]),
                "revenue_inr_crore": float(row["Tourism Revenue (INR Crore)"]),
            })
        except (KeyError, ValueError, TypeError):
            continue
    return out


def tourism_summary(state=None, metric="total_tourists"):
    rows = _tourism_rows()
    states = sorted({r["state"] for r in rows})
    if state and state not in states:
        raise ValueError("Unknown state. Choose one of the states returned by this endpoint.")
    if metric not in {"total_tourists", "domestic_tourists", "foreign_tourists", "revenue_inr_crore"}:
        raise ValueError("Unsupported tourism metric.")
    selected = [r for r in rows if not state or r["state"] == state]
    # There is exactly one row per state/month. This is a cross-sectional seasonal profile,
    # not a dated time series; preserve month order but do not infer a year.
    by_month = defaultdict(list)
    for row in selected:
        by_month[row["month"]].append(row)
    chart = []
    for month in MONTHS:
        vals = [r[metric] for r in by_month.get(month, [])]
        chart.append({"month": month, "value": round(sum(vals) / len(vals), 2) if vals else None,
                      "observations": len(vals)})
    return {
        "kind": "historical_monthly_summary",
        "label": "Historical monthly profile (year unavailable)",
        "metric": metric, "state": state,
        "data_coverage": {"records": len(rows), "states": len(states), "months_per_state": 12,
                          "year_available": False, "filtered_records": len(selected)},
        "evaluation": None,
        "limitations": ["The workbook contains no year field and its source row order is state/month grouping, not chronology.",
                        "Values are historical cross-sectional summaries, not future forecasts."],
        "series": chart,
        "states": states,
        "totals_consistent": all(r["total_tourists"] == r["domestic_tourists"] + r["foreign_tourists"] for r in rows),
    }


def government_overview():
    """Consistent source-level aggregates; calendar month is not a dated timeline."""
    rows = _tourism_rows()
    by_month = defaultdict(lambda: {"domestic_tourists": 0, "foreign_tourists": 0,
                                    "total_tourists": 0, "revenue_inr_crore": 0.0,
                                    "observations": 0})
    for row in rows:
        bucket = by_month[row["month"]]
        for metric in ("domestic_tourists", "foreign_tourists", "total_tourists", "revenue_inr_crore"):
            bucket[metric] += row[metric]
        bucket["observations"] += 1
    return {
        "kind": "cross_sectional_monthly_aggregates",
        "coverage": {"records": len(rows), "states": len({r["state"] for r in rows}),
                     "months": 12, "year_available": False},
        "series": [{"month": month, **by_month[month]} for month in MONTHS],
        "totals_consistent": all(r["total_tourists"] == r["domestic_tourists"] + r["foreign_tourists"] for r in rows),
        "limitation": "Rows are grouped by month/state with no year. Monthly sums are cross-sectional source aggregates, not latest/current values or a forecast.",
    }
