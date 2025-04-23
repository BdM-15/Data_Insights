"""
Utility functions for the Data_Insights application.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

def read_file(file_path: str) -> Optional[str]:
    """
    Read the content of a file and return it as a string.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File content as string, or None if file doesn't exist
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return None

def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        print(f"Error writing to file {file_path}: {str(e)}")
        return False

def format_currency(value: float) -> str:
    """
    Format a numeric value as currency.
    
    Args:
        value: Numeric value to format
        
    Returns:
        Formatted currency string
    """
    if pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"

def extract_rules_from_planning(content: str) -> Dict[str, Any]:
    """
    Extract rules and guidelines from planning document content.
    
    Args:
        content: String content of planning document
        
    Returns:
        Dictionary containing extracted rules and guidelines
    """
    # Implementation for extracting rules from planning documents
    # This would parse markdown/text to extract structured information
    
    # Placeholder implementation
    rules = {
        "coding_standards": [],
        "architecture_guidelines": [],
        "database_rules": []
    }
    
    return rules

def extract_tasks_from_tasks(content):
    """Extracts tasks from the TASKS.md content."""
    tasks = []
    if content:
        # Example: Extract tasks as bullet points
        lines = content.splitlines()
        for line in lines:
            if line.strip().startswith("-"):
                tasks.append(line.strip())
    return tasks

def extract_insights_from_captureintel(content):
    """Extracts insights from the CAPTUREINTEL.md content."""
    insights = {}
    if content:
        # Example: Extract sections based on headers
        lines = content.splitlines()
        current_section = None
        for line in lines:
            if line.startswith("##"):
                current_section = line.strip("# ").strip()
                insights[current_section] = []
            elif current_section and line.strip():
                insights[current_section].append(line.strip())
    return insights

# Fiscal year/quarter calculation functions
def calculate_fiscal_year_quarter(dates) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate fiscal year and fiscal quarter for a series of dates.
    
    The federal fiscal year runs from October 1 to September 30.
    Q1: Oct, Nov, Dec
    Q2: Jan, Feb, Mar
    Q3: Apr, May, Jun
    Q4: Jul, Aug, Sep
    
    Args:
        dates: Pandas Series of datetime objects
        
    Returns:
        Tuple of (fiscal_years, fiscal_quarters) pandas Series
    """
    # Convert to pandas datetime if not already
    dates = pd.to_datetime(dates)
    
    # Extract month and year
    month = dates.dt.month
    year = dates.dt.year
    
    # Assign fiscal year
    # Reason: If month is October or later, fiscal year is next calendar year
    fiscal_years = year.copy()
    fiscal_years = year.where(month < 10, year + 1)
    
    # Assign fiscal quarter
    # Reason: Convert calendar months to fiscal quarters
    # Oct-Dec: Q1, Jan-Mar: Q2, Apr-Jun: Q3, Jul-Sep: Q4
    fiscal_quarters = pd.Series(index=dates.index, dtype='int64')
    fiscal_quarters = fiscal_quarters.mask(month.isin([10, 11, 12]), 1)
    fiscal_quarters = fiscal_quarters.mask(month.isin([1, 2, 3]), 2)
    fiscal_quarters = fiscal_quarters.mask(month.isin([4, 5, 6]), 3)
    fiscal_quarters = fiscal_quarters.mask(month.isin([7, 8, 9]), 4)
    
    return fiscal_years, fiscal_quarters

def generate_fiscal_quarters(start_date, end_date) -> List[Tuple[int, int, str]]:
    """
    Generate all fiscal quarters between start_date and end_date.
    
    Args:
        start_date: Start date (datetime or string)
        end_date: End date (datetime or string)
        
    Returns:
        List of tuples (fiscal_year, fiscal_quarter, display_name)
    """
    # Convert to datetime if string
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
    
    # Create a date range with monthly frequency
    date_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    # Extract unique fiscal year/quarter combinations
    fy, fq = calculate_fiscal_year_quarter(date_range)
    quarters = pd.DataFrame({'fiscal_year': fy, 'fiscal_quarter': fq, 'date': date_range})
    unique_quarters = quarters.drop_duplicates(['fiscal_year', 'fiscal_quarter'])
    
    # Create display names and sort by fiscal year and quarter
    unique_quarters['display_name'] = 'FY' + unique_quarters['fiscal_year'].astype(str) + ' Q' + unique_quarters['fiscal_quarter'].astype(str)
    unique_quarters = unique_quarters.sort_values(['fiscal_year', 'fiscal_quarter'])
    
    # Return as list of tuples
    return [
        (row.fiscal_year, row.fiscal_quarter, row.display_name) 
        for _, row in unique_quarters.iterrows()
    ]

def main():
    # Define file paths
    planning_path = "PLANNING.md"
    tasks_path = "TASKS.md"
    captureintel_path = "CAPTUREINTEL.md"

    # Read files
    planning_content = read_file(planning_path)
    tasks_content = read_file(tasks_path)
    captureintel_content = read_file(captureintel_path)

    # Extract rules and tasks
    planning_rules = extract_rules_from_planning(planning_content)
    tasks = extract_tasks_from_tasks(tasks_content)
    captureintel_insights = extract_insights_from_captureintel(captureintel_content)  # Updated to use new extraction logic

    # Print extracted information (for debugging or further use)
    print("Extracted Rules from PLANNING.md:")
    print(planning_rules)
    print("\nExtracted Tasks from TASKS.md:")
    print(tasks)
    print("\nExtracted Insights from CAPTUREINTEL.md:")
    print(captureintel_insights)

# Updated to include WORKSPACERULES.md in the review process

def save_parsed_context(parsed_data, output_file="context.json"):
    """Saves parsed data into a JSON file for persistent context."""
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(parsed_data, json_file, indent=4)

def review_files():
    files_to_review = {
        "docs/PLANNING.md": extract_rules_from_planning,
        "docs/TASKS.md": extract_tasks_from_tasks,
        "docs/WORKSPACERULES.md": lambda content: {"rules": content.splitlines()},
        "docs/CAPTUREINTEL.md": extract_insights_from_captureintel,
    }

    parsed_context = {}

    for file, parser in files_to_review.items():
        print(f"Reviewing {file}...")
        content = read_file(file)
        if content:
            parsed_data = parser(content)
            parsed_context[file] = parsed_data
            print(f"Extracted data from {file}:")
            print(parsed_data)
        else:
            print(f"Could not read {file} or file is empty.")

    # Save the parsed context to a JSON file
    save_parsed_context(parsed_context)
    print("\nParsed context saved to 'context.json'.")

if __name__ == "__main__":
    review_files()