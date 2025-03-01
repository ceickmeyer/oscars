import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
import base64
from io import BytesIO
import os

# Load the data
df = pd.read_csv('oscar_votes.csv')

def truncate_title(title, max_length=30):
    """Truncate long titles for better visualization."""
    if len(title) > max_length:
        return title[:max_length-3] + '...'
    return title

def process_category(df, category_pattern):
    """Process votes for a specific category."""
    # Get columns matching the pattern
    category_cols = [col for col in df.columns if re.search(category_pattern, col)]
    
    # Skip if no columns found
    if not category_cols:
        return None
    
    # Extract votes for each nominee
    results = {}
    
    for col in category_cols:
        # Extract nominee name from column header
        match = re.search(r'\[(.*?)\]', col)
        if not match:
            continue
            
        nominee = match.group(1)
        
        # Process votes in this column
        for vote in df[col].dropna():
            if isinstance(vote, str) and 'points' in vote:
                # Split multiple point allocations if present
                point_allocations = vote.split(',')
                
                for allocation in point_allocations:
                    allocation = allocation.strip()
                    points = int(re.search(r'(\d+)', allocation).group(1))
                    
                    if nominee in results:
                        results[nominee] += points
                    else:
                        results[nominee] = points
    
    # Convert to DataFrame for easier plotting
    results_df = pd.DataFrame({
        'Nominee': list(results.keys()),
        'Points': list(results.values())
    }).sort_values('Points', ascending=False)
    
    return results_df

def plot_to_base64(plt):
    """Convert matplotlib plot to base64 string for HTML embedding."""
    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')

def plot_category(category_name, pattern, figsize=(12, 8), return_base64=False):
    """Create a bar chart for a specific category."""
    results = process_category(df, pattern)
    
    if results is None or len(results) == 0:
        print(f"No data found for {category_name}")
        return None, None
        
    plt.figure(figsize=figsize)
    
    # Create bar plot with Seaborn for better styling
    ax = sns.barplot(x='Points', y='Nominee', data=results, palette='viridis')
    
    # Add point values as text on the bars
    for i, v in enumerate(results['Points']):
        ax.text(v + 5, i, str(v), va='center')
    
    plt.title(f'Oscar Votes: {truncate_title(category_name)}', fontsize=16)
    plt.xlabel('Total Points', fontsize=12)
    plt.ylabel('Nominee', fontsize=12)
    plt.tight_layout()
    
    if return_base64:
        img_str = plot_to_base64(plt)
        plt.close()
        return img_str, results
    else:
        plt.savefig(f"visualizations/{category_name.replace(' ', '_')}.png")
        plt.close()
        return None, results

def plot_top_categories(n_categories=5, n_nominees=5, return_base64=False):
    """Create a multi-category visualization showing top nominees."""
    categories = [
        ("Best Picture", r"Best Picture.*\["),
        ("Best Director", r"Best Director.*\["),
        ("Best Actor", r"Best Actor \(90.*\["),
        ("Best Actress", r"Best Actress \(90.*\["),
        ("Best Original Screenplay", r"Best Original Screenplay.*\["),
        ("Best Adapted Screenplay", r"Best Adapted Screenplay.*\["),
        ("Best Supporting Actor", r"Best Supporting Actor.*\["),
        ("Best Supporting Actress", r"Best Supporting Actress.*\[")
    ]
    
    fig, axes = plt.subplots(n_categories, 1, figsize=(12, 5 * n_categories))
    
    for i, (cat_name, pattern) in enumerate(categories[:n_categories]):
        results = process_category(df, pattern)
        
        if results is None or len(results) == 0:
            continue
            
        # Limit to top n nominees
        results = results.head(n_nominees)
        
        ax = axes[i]
        sns.barplot(x='Points', y='Nominee', data=results, palette='viridis', ax=ax)
        
        # Add point values
        for j, v in enumerate(results['Points']):
            ax.text(v + 5, j, str(v), va='center')
        
        ax.set_title(truncate_title(cat_name))
        ax.set_xlabel('Points')
        
    plt.tight_layout()
    
    if return_base64:
        img_str = plot_to_base64(plt)
        plt.close()
        return img_str
    else:
        plt.savefig("visualizations/top_categories.png")
        plt.close()
        return None

def generate_heatmap(top_n=10, return_base64=False):
    """Create a heatmap of top nominees across major categories."""
    main_categories = [
        ("Best Picture", r"Best Picture.*\["),
        ("Best Director", r"Best Director.*\["),
        ("Best Actor", r"Best Actor \(90.*\["),
        ("Best Actress", r"Best Actress \(90.*\["),
        ("Best Supporting Actor", r"Best Supporting Actor.*\["),
        ("Best Supporting Actress", r"Best Supporting Actress.*\[")
    ]
    
    # Get top nominees and their films
    all_nominees = {}
    films = set()
    
    for cat_name, pattern in main_categories:
        results = process_category(df, pattern)
        if results is not None and len(results) > 0:
            all_nominees[cat_name] = results
            
            # Extract film names from nominees where applicable
            if cat_name in ["Best Actor", "Best Actress", "Best Supporting Actor", "Best Supporting Actress"]:
                for nominee in results['Nominee']:
                    parts = nominee.split(',')
                    if len(parts) > 1:
                        films.add(parts[1].strip())
    
    # Create matrix for heatmap
    top_films = list(films)[:top_n]
    categories = list(all_nominees.keys())
    
    matrix = np.zeros((len(categories), len(top_films)))
    
    for i, category in enumerate(categories):
        for j, film in enumerate(top_films):
            for idx, nominee in enumerate(all_nominees[category]['Nominee']):
                if film in nominee:
                    matrix[i, j] = all_nominees[category]['Points'].iloc[idx]
    
    # Plot heatmap
    plt.figure(figsize=(15, 10))
    sns.heatmap(matrix, annot=True, fmt='.0f', cmap='viridis',
                xticklabels=top_films, yticklabels=categories)
    plt.title('Points by Film and Category', fontsize=16)
    plt.tight_layout()
    
    if return_base64:
        img_str = plot_to_base64(plt)
        plt.close()
        return img_str
    else:
        plt.savefig("visualizations/category_film_heatmap.png")
        plt.close()
        return None

def analyze_total_points_by_film(return_base64=False):
    """Analyze and visualize total points by film across all categories."""
    # Get all columns with points
    point_cols = [col for col in df.columns if ']' in col]
    
    # Initialize dictionary to store film points
    film_points = {}
    
    # Process each column
    for col in point_cols:
        # Extract the film/nominee info from the column name
        match = re.search(r'\[(.*?)\]', col)
        if not match:
            continue
            
        nominee_info = match.group(1)
        
        # Try to extract the film name
        film = None
        if ',' in nominee_info:
            # For acting categories: "Actor Name, Film Name"
            parts = nominee_info.split(',')
            if len(parts) > 1:
                film = parts[1].strip()
        else:
            # For Best Picture: just the film name
            film = nominee_info
        
        if not film:
            continue
            
        # Process votes in this column
        for vote in df[col].dropna():
            if isinstance(vote, str) and 'points' in vote:
                # Split multiple point allocations if present
                point_allocations = vote.split(',')
                
                for allocation in point_allocations:
                    allocation = allocation.strip()
                    points = int(re.search(r'(\d+)', allocation).group(1))
                    
                    if film in film_points:
                        film_points[film] += points
                    else:
                        film_points[film] = points
    
    # Convert to DataFrame and sort
    results_df = pd.DataFrame({
        'Film': list(film_points.keys()),
        'Total Points': list(film_points.values())
    }).sort_values('Total Points', ascending=False)
    
    # Filter to only include Best Picture nominees
    best_picture_nominees = process_category(df, r"Best Picture.*\[")
    if best_picture_nominees is not None:
        best_picture_films = best_picture_nominees['Nominee'].tolist()
        results_df = results_df[results_df['Film'].isin(best_picture_films)]
    
    # Plot the results
    plt.figure(figsize=(12, 10))
    ax = sns.barplot(x='Total Points', y='Film', data=results_df.head(15), palette='viridis')
    
    # Add point values as text
    for i, v in enumerate(results_df.head(15)['Total Points']):
        ax.text(v + 5, i, str(v), va='center')
    
    plt.title('Oscar Votes: Total Points by Film (Top 15)', fontsize=16)
    plt.xlabel('Total Points', fontsize=12)
    plt.ylabel('Film', fontsize=12)
    plt.tight_layout()
    
    if return_base64:
        img_str = plot_to_base64(plt)
        plt.close()
        return img_str, results_df
    else:
        plt.savefig("visualizations/total_points_by_film.png")
        plt.close()
        return None, results_df

def generate_html():
    """Generate a single HTML file with all visualizations."""
    print("Generating HTML with all visualizations...")
    
    # Create visualizations directory if it doesn't exist
    if not os.path.exists('visualizations'):
        os.makedirs('visualizations')
    
    # Define major categories
    major_categories = [
        ("Best Picture", r"Best Picture.*\["),
        ("Best Director", r"Best Director.*\["),
        ("Best Actor", r"Best Actor \(90.*\["),
        ("Best Actress", r"Best Actress \(90.*\["),
        ("Best Original Screenplay", r"Best Original Screenplay.*\["),
        ("Best Adapted Screenplay", r"Best Adapted Screenplay.*\["),
        ("Best Supporting Actor", r"Best Supporting Actor.*\["),
        ("Best Supporting Actress", r"Best Supporting Actress.*\["),
        ("Best International Feature", r"Best International Feature.*\["),
        ("Best Animated Feature", r"Best Animated Feature.*\["),
        ("Best Visual Effects", r"Best Visual Effects.*\["),
        ("Best Cinematography", r"Best Cinematography.*\[")
    ]
    
    # Generate all visualizations as base64 strings
    category_images = []
    for cat_name, pattern in major_categories:
        print(f"Processing {cat_name} for HTML...")
        img_str, results = plot_category(cat_name, pattern, return_base64=True)
        if img_str is not None:
            if results is not None and len(results) > 0:
                winner = results.iloc[0]['Nominee']
                points = results.iloc[0]['Points']
                category_images.append((cat_name, img_str, winner, points))
    
    print("Generating top categories summary for HTML...")
    top_categories_img = plot_top_categories(return_base64=True)
    
    print("Analyzing total points by film for HTML...")
    total_points_img, film_results = analyze_total_points_by_film(return_base64=True)
    
    print("Generating category-film heatmap for HTML...")
    heatmap_img = generate_heatmap(return_base64=True)
    
    # Create HTML content
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Oscar Votes Analysis</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                border-radius: 5px;
            }}
            h1, h2, h3 {{
                color: #333;
            }}
            .section {{
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }}
            .chart-container {{
                text-align: center;
                margin: 20px 0;
                overflow-x: auto;
            }}
            .chart {{
                max-width: 100%;
                height: auto;
            }}
            .winner-card {{
                background-color: #f9f9f9;
                border-left: 4px solid #4CAF50;
                padding: 10px 15px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .nav {{
                position: sticky;
                top: 0;
                background-color: white;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
                margin-bottom: 20px;
                z-index: 100;
            }}
            .nav-links {{
                display: flex;
                gap: 15px;
                overflow-x: auto;
                padding-bottom: 5px;
            }}
            .nav-link {{
                white-space: nowrap;
                color: #0066cc;
                text-decoration: none;
            }}
            .nav-link:hover {{
                text-decoration: underline;
            }}
            @media (max-width: 768px) {{
                .container {{
                    padding: 10px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Oscar Votes Analysis</h1>
            
            <div class="nav">
                <div class="nav-links">
                    <a href="#summary" class="nav-link">Summary</a>
                    <a href="#top-film" class="nav-link">Top Films</a>
                    <a href="#heatmap" class="nav-link">Category-Film Heatmap</a>
                    <a href="#categories" class="nav-link">Individual Categories</a>
                </div>
            </div>
            
            <div id="summary" class="section">
                <h2>Top Categories Summary</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{top_categories_img}" alt="Top Categories Summary" class="chart">
                </div>
            </div>
            
            <div id="top-film" class="section">
                <h2>Total Points by Film</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{total_points_img}" alt="Total Points by Film" class="chart">
                </div>
                
                <h3>Top 5 Films by Total Points</h3>
                <table>
                    <tr>
                        <th>Rank</th>
                        <th>Film</th>
                        <th>Total Points</th>
                    </tr>
    '''
    
    # Add top 5 films to the table
    for i, (_, row) in enumerate(film_results.head(5).iterrows()):
        html_content += f'''
                    <tr>
                        <td>{i+1}</td>
                        <td>{row['Film']}</td>
                        <td>{row['Total Points']}</td>
                    </tr>
        '''
    
    html_content += '''
                </table>
            </div>
            
            <div id="heatmap" class="section">
                <h2>Category-Film Heatmap</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{}" alt="Category-Film Heatmap" class="chart">
                </div>
            </div>
            
            <div id="categories" class="section">
                <h2>Individual Categories</h2>
    '''.format(heatmap_img)
    
    # Add all category visualizations
    for cat_name, img_str, winner, points in category_images:
        cat_id = cat_name.replace(' ', '_').lower()
        html_content += f'''
                <div id="{cat_id}" class="section">
                    <h3>{cat_name}</h3>
                    <div class="winner-card">
                        <strong>Current Leader:</strong> {winner} with {points} points
                    </div>
                    <div class="chart-container">
                        <img src="data:image/png;base64,{img_str}" alt="{cat_name}" class="chart">
                    </div>
                </div>
        '''
    
    html_content += '''
            </div>
            
            <div class="section">
                <h2>About This Analysis</h2>
                <p>This analysis is based on the Oscar votes where each voter gets two votes: 
                   the first vote is worth twice as much as the second. Voters can split their votes 
                   between candidates or put both onto the same candidate.</p>
                <p>Generated on: {}</p>
            </div>
        </div>
    </body>
    </html>
    '''.format(pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Write HTML to file
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("HTML file generated: index.html")

# Main execution
def main():
    print("Generating visualizations for Oscar votes...")
    
    # Create visualizations directory if it doesn't exist
    if not os.path.exists('visualizations'):
        os.makedirs('visualizations')
    
    # Generate individual PNG files for major categories
    major_categories = [
        ("Best Picture", r"Best Picture.*\["),
        ("Best Director", r"Best Director.*\["),
        ("Best Actor", r"Best Actor \(90.*\["),
        ("Best Actress", r"Best Actress \(90.*\["),
        ("Best Original Screenplay", r"Best Original Screenplay.*\["),
        ("Best Adapted Screenplay", r"Best Adapted Screenplay.*\["),
        ("Best Supporting Actor", r"Best Supporting Actor.*\["),
        ("Best Supporting Actress", r"Best Supporting Actress.*\["),
        ("Best International Feature", r"Best International Feature.*\["),
        ("Best Animated Feature", r"Best Animated Feature.*\[")
    ]
    
    for cat_name, pattern in major_categories:
        print(f"Processing {cat_name}...")
        _, results = plot_category(cat_name, pattern)
        if results is not None and len(results) > 0:
            print(f"Top nominee: {results.iloc[0]['Nominee']} with {results.iloc[0]['Points']} points")
    
    # Generate the top categories summary
    print("Generating top categories summary...")
    plot_top_categories()
    
    # Generate film-based analysis
    print("Analyzing total points by film...")
    _, film_results = analyze_total_points_by_film()
    print(f"Top film: {film_results.iloc[0]['Film']} with {film_results.iloc[0]['Total Points']} points")
    
    # Generate heatmap
    print("Generating category-film heatmap...")
    generate_heatmap()
    
    # Generate comprehensive HTML file
    generate_html()
    
    print("All visualizations complete!")

if __name__ == "__main__":
    main()