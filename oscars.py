import pandas as pd
import os
import re
import json
from collections import defaultdict

def preprocess_columns(df):
    """Extract category, points possible, and nominee from each column header and preserve category order."""
    columns_info = []
    category_order = []  # To preserve the order of categories as they appear in the CSV
    category_points_possible = {}
    seen_categories = set()  # To avoid duplicates

    # Updated regex to capture category, points possible, and nominee
    header_regex = r'^(.*?)\s*\((\d+)\s*points\s*possible\)\s*\["?(.*?)"?\]$'

    for col in df.columns:
        if col in ["Timestamp", "Email Address"]:
            continue

        match = re.match(header_regex, col)
        if match:
            category = match.group(1).strip()
            points_possible = int(match.group(2).strip())
            nominee = match.group(3).strip()
        else:
            # Fallback for unexpected formats
            category = col.split('[')[0].split('(')[0].strip()
            nominee = col
            points_possible = 0

        columns_info.append((category, points_possible, nominee))

        # Track category order and store points possible (first encountered wins)
        if category not in seen_categories:
            seen_categories.add(category)
            category_order.append(category)
            category_points_possible[category] = points_possible

    return columns_info, category_order, category_points_possible

def parse_points(value):
    """Parse and sum points from a cell value."""
    points = re.findall(r'(\d+)\s*points?', str(value))
    return sum(int(p) for p in points) if points else 0

def generate_html_content(email, user_votes, category_order, category_points_possible):
    """Generate HTML content with grouped categories and combined points, preserving category order."""
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oscar Votes for {email}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #fff;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            color: #b8860b;
            font-size: 1.5em;
        }}
        .ballot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .category {{
            border: 1px solid #d4c485;
            background-color: #fff;
            padding: 15px;
            margin-bottom: 0px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            break-inside: avoid;
        }}
        .category-title {{
            color: #b8860b;
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            border-bottom: 1px solid #d4c485;
            padding-bottom: 5px;
        }}
        .nominee {{
            margin-bottom: 8px;
            padding: 8px;
            background-color: #f9f5e8;
            border-radius: 4px;
        }}
        .nominee-text {{
            font-size: 0.9em;
            color: #333;
            line-height: 1.4;
        }}
        .points {{
            font-weight: bold;
            color: #666;
            margin-left: 5px;
        }}
    </style>
</head>
<body>
    <div class="header">Oscar Votes for {email}</div>
    <div class="header"><a href="../index.html">Who Voted for What</a></div>
    <div class="ballot-grid">
        {categories_html}
    </div>
</body>
</html>
"""
    categories_html = []
    
    # Use the preserved category order
    for category in category_order:
        nominees = user_votes.get(category, {})
        if not nominees:
            continue
        
        # Build the category header with points possible (if available)
        points_possible = category_points_possible.get(category, 0)
        category_header = f"{category} - {points_possible} Points" if points_possible else category
        
        category_block = [f'<div class="category"><div class="category-title">{category_header}</div>']
        
        # Sort nominees by points descending, then by name ascending
        sorted_nominees = sorted(nominees.items(), key=lambda x: (-x[1], x[0]))
        
        for nominee, points in sorted_nominees:
            category_block.append(f'''
                <div class="nominee">
                    <div class="nominee-text">
                        {nominee}
                        <span class="points">({points} points)</span>
                    </div>
                </div>
            ''')
        
        category_block.append('</div>')
        categories_html.append('\n'.join(category_block))
    
    return html_template.format(
        email=email,
        categories_html='\n'.join(categories_html)
    )

# Main processing
file_path = "oscar_votes.csv"
df = pd.read_csv(file_path)

# Preprocess column headers to get category, points possible, and nominee, and preserve category order
columns_info, category_order, category_points_possible = preprocess_columns(df)

output_dir = "user_votes"
os.makedirs(output_dir, exist_ok=True)

# List to store details about generated files for the index and JSON
generated_files = []

for index, row in df.iterrows():
    email = row["Email Address"].strip()
    if not email:
        continue
    
    user_votes = defaultdict(lambda: defaultdict(int))
    
    # Iterate through each data column (skipping Timestamp and Email Address)
    for i in range(2, len(row)):
        category, _, nominee = columns_info[i-2]  # Adjust index since columns_info skips first two
        cell_value = row[i]
        points = parse_points(cell_value)
        if points > 0:
            user_votes[category][nominee] += points
    
    # Generate HTML content, passing the preserved category order and points mapping
    html_content = generate_html_content(email, user_votes, category_order, category_points_possible)
    
    # Save to file using a safe filename format
    safe_email = email.replace('@', '_at_').replace('.', '_dot_')
    file_name = f"{safe_email}.html"
    file_path_full = os.path.join(output_dir, file_name)
    with open(file_path_full, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Record this file's details for later use
    generated_files.append({"email": email, "file": file_name})

print("HTML files generated successfully.")

# Create an index HTML file linking to all generated HTML files.
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Index of Oscar Votes</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: #b8860b; }
        ul { list-style: none; padding: 0; }
        li { margin-bottom: 10px; }
        a { text-decoration: none; color: #333; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Index of Oscar Votes</h1>
    <ul>
"""

for entry in generated_files:
    # The links are relative to the output directory
    index_html += f'        <li><a href="{entry["file"]}">{entry["email"]}</a></li>\n'

index_html += """
    </ul>
</body>
</html>
"""

with open(os.path.join(output_dir, "index.html"), "w", encoding='utf-8') as f:
    f.write(index_html)

print("Index HTML file created successfully.")

# Create a JSON file that maps each email to its HTML file.
with open(os.path.join(output_dir, "votes.json"), "w", encoding='utf-8') as f:
    json.dump(generated_files, f, indent=4)

print("JSON file created successfully.")
