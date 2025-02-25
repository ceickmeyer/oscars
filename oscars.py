import pandas as pd
import os
import re
from collections import defaultdict, OrderedDict

def preprocess_columns(df):
    """Extract category and nominee from each column header and preserve category order."""
    columns_info = []
    category_order = []  # To preserve the order of categories as they appear in the CSV
    seen_categories = set()  # To avoid duplicates

    for col in df.columns:
        if col in ["Timestamp", "Email Address"]:
            continue
        # Regex to capture category and nominee
        match = re.match(
            r'^(.*?)\s*\(\d+\s*points\s*possible\)\s*\["?(.*?)"?\]$',
            col
        )
        if match:
            category = match.group(1).strip()
            nominee = match.group(2).strip()
            # Remove quotes around nominee if present
            nominee = re.sub(r'^"|"$', '', nominee)
        else:
            # Fallback for unexpected formats
            category = col.split('[')[0].split('(')[0].strip()
            nominee = col

        columns_info.append((category, nominee))

        # Track category order
        if category not in seen_categories:
            seen_categories.add(category)
            category_order.append(category)

    return columns_info, category_order

def parse_points(value):
    """Parse and sum points from a cell value."""
    points = re.findall(r'(\d+)\s*points?', str(value))
    return sum(int(p) for p in points) if points else 0

def generate_html_content(email, user_votes, category_order):
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
            font-family: "Times New Roman", serif;
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
            text-transform: uppercase;
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
        
        category_block = [f'<div class="category"><div class="category-title">{category}</div>']
        
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

# Preprocess column headers to get category and nominee, and preserve category order
columns_info, category_order = preprocess_columns(df)

output_dir = "user_votes"
os.makedirs(output_dir, exist_ok=True)

for index, row in df.iterrows():
    email = row["Email Address"].strip()
    if not email:
        continue
    
    user_votes = defaultdict(lambda: defaultdict(int))
    
    # Iterate through each data column (skipping Timestamp and Email)
    for i in range(2, len(row)):
        category, nominee = columns_info[i-2]  # Adjust index since columns_info skips first two
        cell_value = row[i]
        points = parse_points(cell_value)
        if points > 0:
            user_votes[category][nominee] += points
    
    # Generate HTML content, passing the preserved category order
    html_content = generate_html_content(email, user_votes, category_order)
    
    # Save to file
    safe_email = email.replace('@', '_at_').replace('.', '_dot_')
    file_name = os.path.join(output_dir, f"{safe_email}.html")
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(html_content)

print("HTML files generated successfully.")