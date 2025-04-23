"""
Export functionality components for the Data_Insights application.

This module provides functions to export data in various formats,
supporting the business intelligence needs of defense contractors.
"""

import streamlit as st
import pandas as pd
import base64
import io
from typing import Optional

def create_download_button(
    df: pd.DataFrame, 
    button_text: str = "Download CSV", 
    file_name: str = "data.csv"
) -> None:
    """
    Create a download button for a DataFrame.
    
    Args:
        df: pandas DataFrame to export
        button_text: Text to display on the button
        file_name: Name of the file to download
        
    Returns:
        None
    """
    # Convert DataFrame to CSV
    csv = df.to_csv(index=False)
    
    # Create a download button
    st.download_button(
        label=button_text,
        data=csv,
        file_name=file_name,
        mime="text/csv"
    )
    
def export_to_excel(
    df: pd.DataFrame, 
    file_name: str = "data.xlsx"
) -> str:
    """
    Export DataFrame to Excel and provide a download link.
    
    Args:
        df: pandas DataFrame to export
        file_name: Name of the file to download
        
    Returns:
        Download link HTML
    """
    # Create a BytesIO buffer for Excel data
    output = io.BytesIO()
    
    # Write DataFrame to Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
        
    # Get the binary data and encode as base64
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    
    # Create download link
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{file_name}">Download Excel file</a>'
    
    return href

def format_dataframe_for_export(
    df: pd.DataFrame, 
    currency_columns: Optional[list] = None
) -> pd.DataFrame:
    """
    Format a DataFrame for export, ensuring proper data types and formatting.
    
    Args:
        df: Input DataFrame to format
        currency_columns: List of column names to format as currency
        
    Returns:
        Formatted DataFrame ready for export
    """
    # Create a copy of the DataFrame to avoid modifying the original
    export_df = df.copy()
    
    # Format currency columns if specified
    if currency_columns:
        for col in currency_columns:
            if col in export_df.columns:
                # Ensure numeric type
                export_df[col] = pd.to_numeric(export_df[col], errors='coerce')
                
                # Create a formatted column for display
                # Reason: We keep the numeric values for Excel but format for CSV
                if export_df[col].dtype == 'float64':
                    export_df[col] = export_df[col].map('${:,.2f}'.format)
    
    # Convert datetime columns to string in ISO format
    for col in export_df.select_dtypes(include=['datetime64']).columns:
        export_df[col] = export_df[col].dt.strftime('%Y-%m-%d')
    
    return export_df

def add_export_section(
    df: pd.DataFrame, 
    section_title: str = "Export Data",
    file_prefix: str = "data"
) -> None:
    """
    Add data export options to the Streamlit interface.
    
    Args:
        df: DataFrame to export
        section_title: Title for the export section
        file_prefix: Prefix for exported filenames
        
    Returns:
        None
    """
    st.subheader(section_title)
    
    col1, col2 = st.columns(2)
    
    # Get today's date for filename
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    
    with col1:
        # CSV download
        create_download_button(
            df, 
            "Download CSV", 
            f"{file_prefix}_{today}.csv"
        )
    
    with col2:
        # Excel download
        excel_link = export_to_excel(
            df, 
            f"{file_prefix}_{today}.xlsx"
        )
        st.markdown(excel_link, unsafe_allow_html=True)