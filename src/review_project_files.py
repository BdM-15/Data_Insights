import os

def read_file(file_path):
    """Reads the content of a file and returns it as a string."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return None

def extract_rules_from_planning(content):
    """Extracts rules and constraints from the PLANNING.md content."""
    rules = {}
    if content:
        # Example: Extract constraints section
        constraints_start = content.find("## Constraints")
        if constraints_start != -1:
            constraints_end = content.find("##", constraints_start + 1)
            rules['constraints'] = content[constraints_start:constraints_end].strip() if constraints_end != -1 else content[constraints_start:].strip()
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

def review_files():
    files_to_review = {
        "docs/PLANNING.md": extract_rules_from_planning,
        "docs/TASKS.md": extract_tasks_from_tasks,
        "docs/WORKSPACERULES.md": lambda content: {"rules": content.splitlines()},
        "docs/CAPTUREINTEL.md": extract_insights_from_captureintel,
    }

    for file, parser in files_to_review.items():
        print(f"Reviewing {file}...")
        content = read_file(file)
        if content:
            parsed_data = parser(content)
            print(f"Extracted data from {file}:")
            print(parsed_data)
        else:
            print(f"Could not read {file} or file is empty.")

if __name__ == "__main__":
    review_files()