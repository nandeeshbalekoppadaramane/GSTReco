import streamlit as st
import pandas as pd
from io import BytesIO
import os

st.set_page_config(page_title="GST Reconciliation Tool", layout="wide")
st.title("🧾 GSTR-2B vs Tally Reconciliation Tool")

# Sidebar instructions and template download
with st.sidebar:
    st.header("📌 Instructions")
    st.markdown("""
    To use this tool effectively:

    ### ✅ File Format Required
    Both files must follow this format:

    | S.No | GSTIN of Supplier | Trade/Legal Name | Invoice Number | Invoice Date | Invoice Value | Taxable Value | IGST | CGST | SGST |
    |------|-------------------|------------------|----------------|--------------|---------------|---------------|------|------|------|

    - Dates must be in `DD-MM-YYYY` format
    - Values must be numeric (no commas or symbols)
    - GSTIN must be valid and 15-digit

    ### ⚠️ Matching Logic
    We match records based on:
    1. **Invoice Number**
    2. **GSTIN**
    3. **Date**
    4. **Taxable Value**

    If all match → Sheet 1
    If only value differs → Sheet 4
    If Invoice Number matches, but GSTIN or Date differs → Sheet 5
    If not found at all → Sheet 2 or 3
    """)

    st.markdown("---")
    st.markdown("📥 Download Sample Templates")

    col1, col2 = st.columns(2)

    # --- Section for GSTR2B Template Download ---
    with col1:
        gstr2b_template_path = "sample_gstr2b.xlsx"
        # Debugging print statement:
        print(f"Checking for GSTR2B template at: {os.path.abspath(gstr2b_template_path)}")
        if os.path.exists(gstr2b_template_path):
            print(f"GSTR2B template found: {gstr2b_template_path}") # Debugging confirmation
            with open(gstr2b_template_path, "rb") as file:
                st.download_button(
                    label="📄 GSTR2B Template",
                    data=file.read(),
                    file_name="sample_gstr2b.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            print(f"GSTR2B template NOT found: {gstr2b_template_path}") # Debugging error
            st.warning(f"Template file '{gstr2b_template_path}' not found. Ensure it's in the same directory as your script.")
    # --- End of GSTR2B Template Section ---

    # --- Section for Tally Template Download ---
    with col2:
        tally_template_path = "sample_tally.xlsx"
        # Debugging print statement:
        print(f"Checking for Tally template at: {os.path.abspath(tally_template_path)}")
        if os.path.exists(tally_template_path):
            print(f"Tally template found: {tally_template_path}") # Debugging confirmation
            with open(tally_template_path, "rb") as file:
                st.download_button(
                    label="📄 Tally Template",
                    data=file.read(),
                    file_name="sample_tally.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            print(f"Tally template NOT found: {tally_template_path}") # Debugging error
            st.warning(f"Template file '{tally_template_path}' not found. Ensure it's in the same directory as your script.")
    # --- End of Tally Template Section ---

    st.markdown("---")
    st.markdown("© 2025 Nandeesh Balekoppadaramane")
    st.caption("Developed with curiosity using Python & Streamlit")

# File upload section
col1, col2 = st.columns(2)

with col1:
    gstr_file = st.file_uploader("📂 Upload GSTR2B.xlsx", type=["xlsx"])

with col2:
    tally_file = st.file_uploader("📂 Upload Tally.xlsx", type=["xlsx"])

# Helper function to clean string values
def clean_value(value):
    """Helper to clean and convert values to uppercase strings."""
    try:
        return str(value).strip().upper()
    except:
        return ''

# Main processing block
if gstr_file and tally_file:
    if st.button("⚡ Run Reconciliation"):
        with st.spinner("🔄 Processing files... Please wait."):

            # Load data
            try:
                gstr2b_df = pd.read_excel(gstr_file)
                tally_df = pd.read_excel(tally_file)
            except Exception as e:
                st.error(f"❌ Error reading Excel files: {e}")
                st.stop()

            # Normalize column names - strip spaces from all columns
            def normalize_dataframe_columns(df):
                df.columns = df.columns.str.strip()
                return df

            gstr2b_df = normalize_dataframe_columns(gstr2b_df)
            tally_df = normalize_dataframe_columns(tally_df)

            # Ensure required fields exist after normalization
            required_columns = ['S.No', 'GSTIN of Supplier', 'Trade/Legal Name', 'Invoice Number',
                                 'Invoice Date', 'Invoice Value', 'Taxable Value', 'IGST', 'CGST', 'SGST']
            for col in required_columns:
                if col not in gstr2b_df.columns:
                    st.error(f"❌ Missing required column in GSTR2B file: '{col}'. Please ensure column names match the template exactly (e.g., no extra spaces, correct spelling).")
                    st.stop()
                if col not in tally_df.columns:
                    st.error(f"❌ Missing required column in Tally file: '{col}'. Please ensure column names match the template exactly (e.g., no extra spaces, correct spelling).")
                    st.stop()

            # Normalize data (dates, numeric values, string cleaning)
            for df in [gstr2b_df, tally_df]:
                df['Invoice Date'] = pd.to_datetime(df['Invoice Date'], errors='coerce', dayfirst=True).dt.strftime('%d-%m-%Y')
                df['Taxable Value'] = pd.to_numeric(
                    df['Taxable Value'].astype(str).str.replace(r'[^\d.]+', '', regex=True), errors='coerce'
                ).fillna(0)
                df['Invoice Value'] = pd.to_numeric(
                    df['Invoice Value'].astype(str).str.replace(r'[^\d.]+', '', regex=True), errors='coerce'
                ).fillna(0)
                df['IGST'] = pd.to_numeric(df['IGST'], errors='coerce').fillna(0)
                df['CGST'] = pd.to_numeric(df['CGST'], errors='coerce').fillna(0)
                df['SGST'] = pd.to_numeric(df['SGST'], errors='coerce').fillna(0)

                df['Invoice Number'] = df['Invoice Number'].apply(clean_value)
                df['GSTIN of Supplier'] = df['GSTIN of Supplier'].apply(clean_value)

            # Create match keys (important step for merging)
            def create_match_keys(df):
                df['match_key_full'] = (
                    df['Invoice Number'].astype(str) +
                    df['GSTIN of Supplier'].astype(str) +
                    df['Invoice Date'].astype(str).str.replace('-', '') +
                    df['Taxable Value'].astype(str)
                )
                df['match_key_value'] = (
                    df['Invoice Number'].astype(str) +
                    df['GSTIN of Supplier'].astype(str) +
                    df['Invoice Date'].astype(str).str.replace('-', '')
                )
                return df

            gstr2b_df = create_match_keys(gstr2b_df.copy())
            tally_df = create_match_keys(tally_df.copy())

            # Initialize sets to track processed S.No for each sheet to prevent overlaps
            gstr2b_processed_indices = set()
            tally_processed_indices = set()

            # --- Sheet 1: Matched Invoices (Full Match) ---
            sheet1_data = []

            # Merge on the full match key
            merged_full = pd.merge(
                gstr2b_df,
                tally_df,
                on='match_key_full',
                how='inner',
                suffixes=('_GSTR2B', '_Tally') # Columns from original DFs will get these suffixes
            )

            if not merged_full.empty:
                for _, row in merged_full.iterrows():
                    # Populate Sheet 1 data using suffixed column names
                    sheet1_data.append({
                        'GSTR2B S.No': row['S.No_GSTR2B'],
                        'Tally S.No': row['S.No_Tally'],
                        'GSTIN of Supplier': row['GSTIN of Supplier_GSTR2B'], # This refers to GSTR2B's GSTIN
                        'Trade/Legal Name': row['Trade/Legal Name_GSTR2B'],
                        'Invoice Number': row['Invoice Number_GSTR2B'],
                        'Invoice Date': row['Invoice Date_GSTR2B'],
                        'GSTR2B Invoice Value': row['Invoice Value_GSTR2B'],
                        'Tally Invoice Value': row['Invoice Value_Tally'],
                        'Difference: Invoice Value': round(row['Invoice Value_Tally'] - row['Invoice Value_GSTR2B'], 2),
                        'GSTR2B Taxable Value': row['Taxable Value_GSTR2B'],
                        'Tally Taxable Value': row['Taxable Value_Tally'],
                        'Difference: Taxable Value': round(row['Taxable Value_Tally'] - row['Taxable Value_GSTR2B'], 2),
                        'GSTR2B IGST': row['IGST_GSTR2B'],
                        'Tally IGST': row['IGST_Tally'],
                        'Difference: IGST': round(row['IGST_Tally'] - row['IGST_GSTR2B'], 2),
                        'GSTR2B CGST': row['CGST_GSTR2B'],
                        'Tally CGST': row['CGST_Tally'],
                        'Difference: CGST': round(row['CGST_Tally'] - row['CGST_GSTR2B'], 2),
                        'GSTR2B SGST': row['SGST_GSTR2B'],
                        'Tally SGST': row['SGST_Tally'],
                        'Difference: SGST': round(row['SGST_Tally'] - row['SGST_GSTR2B'], 2),
                    })
                    # Add S.No to processed sets
                    gstr2b_processed_indices.add(row['S.No_GSTR2B'])
                    tally_processed_indices.add(row['S.No_Tally'])

            sheet1 = pd.DataFrame(sheet1_data)

            # --- Sheet 4: Value Mismatched ---
            sheet4_data = []

            # Exclude rows already fully matched (Sheet 1) before considering for Sheet 4
            potential_sheet4_gstr = gstr2b_df[~gstr2b_df['S.No'].isin(gstr2b_processed_indices)].copy()
            potential_sheet4_tally = tally_df[~tally_df['S.No'].isin(tally_processed_indices)].copy()

            # Merge on value match key (Inv No, GSTIN, Date)
            merged_value = pd.merge(
                potential_sheet4_gstr,
                potential_sheet4_tally,
                on='match_key_value',
                how='inner',
                suffixes=('_GSTR2B', '_Tally') # Columns from original DFs will get these suffixes
            )

            if not merged_value.empty:
                for _, row in merged_value.iterrows():
                    # Only include if Taxable Value actually differs significantly
                    if abs(row['Taxable Value_GSTR2B'] - row['Taxable Value_Tally']) > 0.01:
                        sheet4_data.append({
                            'GSTR2B S.No': row['S.No_GSTR2B'],
                            'Tally S.No': row['S.No_Tally'],
                            'GSTIN of Supplier': row['GSTIN of Supplier_GSTR2B'],
                            'Trade/Legal Name': row['Trade/Legal Name_GSTR2B'],
                            'Invoice Number': row['Invoice Number_GSTR2B'],
                            'Invoice Date': row['Invoice Date_GSTR2B'],
                            'GSTR2B Invoice Value': row['Invoice Value_GSTR2B'],
                            'Tally Invoice Value': row['Invoice Value_Tally'],
                            'Difference: Invoice Value': round(row['Invoice Value_Tally'] - row['Invoice Value_GSTR2B'], 2),
                            'GSTR2B Taxable Value': row['Taxable Value_GSTR2B'],
                            'Tally Taxable Value': round(row['Taxable Value_Tally'], 2),
                            'Difference: Taxable Value': round(row['Taxable Value_Tally'] - row['Taxable Value_GSTR2B'], 2),
                            'GSTR2B IGST': row['IGST_GSTR2B'],
                            'Tally IGST': row['IGST_Tally'],
                            'Difference: IGST': round(row['IGST_Tally'] - row['IGST_GSTR2B'], 2),
                            'GSTR2B CGST': row['CGST_GSTR2B'],
                            'Tally CGST': row['CGST_Tally'],
                            'Difference: CGST': round(row['CGST_Tally'] - row['CGST_GSTR2B'], 2),
                            'GSTR2B SGST': row['SGST_GSTR2B'],
                            'Tally SGST': row['SGST_Tally'],
                            'Difference: SGST': round(row['SGST_Tally'] - row['SGST_GSTR2B'], 2),
                        })
                        # Add S.No to processed sets
                        gstr2b_processed_indices.add(row['S.No_GSTR2B'])
                        tally_processed_indices.add(row['S.No_Tally'])

            sheet4_df = pd.DataFrame(sheet4_data)

            # --- Sheet 5: Not Matching (Partial Mismatches based on Invoice Number) ---
            sheet5_records = []

            # Filter out records already handled in Sheet 1 and Sheet 4
            gstr2b_remaining = gstr2b_df[~gstr2b_df['S.No'].isin(gstr2b_processed_indices)].copy()
            tally_remaining = tally_df[~tally_df['S.No'].isin(tally_processed_indices)].copy()

            # Merge remaining records based only on Invoice Number
            # Use specific suffixes for this merge to avoid any potential previous suffix conflicts
            merged_invoice_only = pd.merge(
                gstr2b_remaining,
                tally_remaining,
                on='Invoice Number', # Invoice Number is the join key, so it won't be suffixed
                how='inner',
                suffixes=('_GSTR2B_S5', '_Tally_S5') # Other columns will get these suffixes
            )

            if not merged_invoice_only.empty:
                for _, row in merged_invoice_only.iterrows():
                    # Identify specific mismatches for Sheet 5 (GSTIN, Date, or Taxable Value difference)
                    is_gstin_mismatch = row['GSTIN of Supplier_GSTR2B_S5'] != row['GSTIN of Supplier_Tally_S5']
                    is_date_mismatch = row['Invoice Date_GSTR2B_S5'] != row['Invoice Date_Tally_S5']
                    is_taxable_value_mismatch = abs(row['Taxable Value_GSTR2B_S5'] - row['Taxable Value_Tally_S5']) > 0.01

                    # If any of these mismatches exist, add to Sheet 5
                    if is_gstin_mismatch or is_date_mismatch or is_taxable_value_mismatch:
                        mismatch_reason_parts = []
                        if is_gstin_mismatch:
                            mismatch_reason_parts.append("GSTIN mismatch")
                        if is_date_mismatch:
                            mismatch_reason_parts.append("Date mismatch")
                        if is_taxable_value_mismatch:
                            mismatch_reason_parts.append("Taxable Value mismatch")
                        mismatch_reason = ", ".join(mismatch_reason_parts)

                        sheet5_records.append({
                            'GSTR2B S.No': row['S.No_GSTR2B_S5'],
                            'Tally S.No': row['S.No_Tally_S5'],
                            'Invoice Number': row['Invoice Number'], # Unsuffixed because it was the 'on' key
                            'GSTR2B GSTIN': row['GSTIN of Supplier_GSTR2B_S5'],
                            'Tally GSTIN': row['GSTIN of Supplier_Tally_S5'],
                            'GSTR2B Invoice Date': row['Invoice Date_GSTR2B_S5'],
                            'Tally Invoice Date': row['Invoice Date_Tally_S5'],
                            'GSTR2B Taxable Value': row['Taxable Value_GSTR2B_S5'],
                            'Tally Taxable Value': row['Taxable Value_Tally_S5'],
                            'Mismatch Reason': mismatch_reason
                        })
                        # Add S.No to processed sets
                        gstr2b_processed_indices.add(row['S.No_GSTR2B_S5'])
                        tally_processed_indices.add(row['S.No_Tally_S5'])

            # Remove duplicate pairings (e.g., if one GSTR2B matches multiple Tally entries with same Inv No but different mismatches)
            sheet5_final = pd.DataFrame(sheet5_records).drop_duplicates(subset=['GSTR2B S.No', 'Tally S.No'], keep='first')


            # --- Sheet 2: GSTR2B Only ---
            # GSTR2B records that were not included in Sheet 1, 4, or 5
            sheet2 = gstr2b_df[~gstr2b_df['S.No'].isin(gstr2b_processed_indices)].copy()
            sheet2.insert(0, 'GSTR2B S.No', sheet2.pop('S.No'))
            # Drop internal match key columns for cleaner output
            sheet2 = sheet2.drop(columns=['match_key_full', 'match_key_value'], errors='ignore')

            # --- Sheet 3: Tally Only ---
            # Tally records that were not included in Sheet 1, 4, or 5
            sheet3 = tally_df[~tally_df['S.No'].isin(tally_processed_indices)].copy()
            sheet3.insert(0, 'Tally S.No', sheet3.pop('S.No'))
            # Drop internal match key columns for cleaner output
            sheet3 = sheet3.drop(columns=['match_key_full', 'match_key_value'], errors='ignore')


            # Write all results to a single Excel file with multiple sheets
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if not sheet1.empty:
                    sheet1.to_excel(writer, sheet_name='Matched Invoices', index=False)
                if not sheet2.empty:
                    sheet2.to_excel(writer, sheet_name='GSTR2B Only', index=False)
                if not sheet3.empty:
                    sheet3.to_excel(writer, sheet_name='Tally Only', index=False)
                if not sheet4_df.empty:
                    sheet4_df.to_excel(writer, sheet_name='Value Mismatched', index=False)
                if not sheet5_final.empty:
                    sheet5_final.to_excel(writer, sheet_name='Not Matching', index=False)

            excel_data = output.getvalue()

            st.success("✅ Reconciliation completed!")

            # Provide download button for the generated report
            st.download_button(
                label="📥 Download Reconciliation Report",
                data=excel_data,
                file_name="reconciliation_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Show previews of the generated sheets
            st.subheader("📊 Preview of Matched Invoices")
            if not sheet1.empty:
                st.dataframe(sheet1.head(), use_container_width=True)
            else:
                st.info("No exact matches found for Sheet 1.")

            if not sheet4_df.empty:
                st.subheader("⚠️ Value Mismatches Found")
                st.dataframe(sheet4_df[['Invoice Number', 'GSTIN of Supplier', 'Difference: Taxable Value']].head(), use_container_width=True)
            else:
                st.info("No value mismatches found for Sheet 4.")

            if not sheet5_final.empty:
                st.subheader("🔍 Not Matching (Partial Mismatches) Preview")
                st.dataframe(sheet5_final[['Invoice Number', 'GSTR2B GSTIN', 'Tally GSTIN', 'Mismatch Reason']].head(), use_container_width=True)
            else:
                st.info("No partial mismatches found for Sheet 5.")

            st.balloons()

else:
    st.info("👆 Please upload both Excel files to start")gst_reconciliation_app.py
