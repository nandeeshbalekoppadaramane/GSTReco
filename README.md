# GSTR-2B vs Tally Reconciliation Tool

A Streamlit app that reconciles your GSTR-2B against your Tally purchase register and splits the result into clear exception sheets, so you can see exactly what matched, what is missing where, and what only partly matches.

## Input format

Both files (GSTR-2B and Tally export) must use the same column layout:

| S.No | GSTIN of Supplier | Trade/Legal Name | Invoice Number | Invoice Date | Invoice Value | Taxable Value | IGST | CGST | SGST |
|------|-------------------|------------------|----------------|--------------|---------------|---------------|------|------|------|

- Dates in `DD-MM-YYYY`
- Numeric values (no commas or symbols)
- Valid 15-digit GSTINs

Sample templates are included in the repo (`sample_gstr2b.xlsx`, `sample_tally.xlsx`) and downloadable from the app sidebar.

## Matching logic

Records are matched on **Invoice Number + GSTIN + Date + Taxable Value**, and every row lands in exactly one output sheet:

| Sheet | Meaning |
|---|---|
| Matched | All four keys match |
| Only in GSTR-2B | Not found in the Tally file at all |
| Only in Tally | Not found in GSTR-2B at all |
| Value mismatch | Invoice found, but taxable/tax values differ |
| Partial match | Invoice number matches, but GSTIN or date differs |

## Run

```bash
pip install -r requirements.txt
streamlit run gst_reconciliation_app.py
```

1. Upload the GSTR-2B Excel and the Tally Excel.
2. Review the summary and per-sheet tables.
3. Download the reconciliation workbook.

Dependencies: `streamlit`, `pandas`, `openpyxl`.

## Notes

- The sample template files must sit next to the script for the sidebar download buttons to appear (the reconciliation itself works without them).
- Everything runs locally; no data leaves your machine.
- Private project.
