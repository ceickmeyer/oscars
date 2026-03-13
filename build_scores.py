import csv
import argparse

INPUT_CSV = "scores.csv"
OUTPUT_HTML = "scores.html"

def obfuscate_name(name):
    parts = name.strip().split()
    if len(parts) >= 2:
        return parts[0] + ' ' + parts[-1][0] + '.'
    return name

def main():
    parser = argparse.ArgumentParser(description='Build Oscars scores page')
    parser.add_argument('--reset', action='store_true', help='Zero out all scores (pre-ceremony reset)')
    args = parser.parse_args()

    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = list(next(reader))

    # Categories are columns 1-24 (between name and Total)
    # Headers: Name, Cat1, Cat2, ..., Cat24, Total, [sorted dupe cols...]
    total_idx = headers.index('Total')
    categories = headers[1:total_idx]

    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        players = []
        for row in reader:
            name_raw = row[0].strip()
            if not name_raw:
                continue
            name = obfuscate_name(name_raw)
            if args.reset:
                total = 0
                cat_scores = {cat: 0 for cat in categories}
            else:
                total = int(row[total_idx]) if row[total_idx].strip().isdigit() else 0
                cat_scores = {}
                for i, cat in enumerate(categories, 1):
                    try:
                        cat_scores[cat] = int(row[i])
                    except (ValueError, IndexError):
                        cat_scores[cat] = 0
            players.append({'name': name, 'total': total, 'cats': cat_scores})

    # Sort by total descending
    players.sort(key=lambda p: p['total'], reverse=True)

    # Assign ranks (handle ties)
    for i, p in enumerate(players):
        if i == 0 or p['total'] != players[i-1]['total']:
            p['rank'] = i + 1
        else:
            p['rank'] = players[i-1]['rank']

    # Medal emoji for top 3
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}

    # Build leaderboard rows
    leaderboard_rows = ''
    for p in players:
        medal = medals.get(p['rank'], '')
        rank_display = f"{medal} {p['rank']}" if medal else str(p['rank'])
        rank_class = f"rank-{min(p['rank'], 4)}"

        # Category breakdown cells — highlight non-zero
        cat_cells = ''
        for cat in categories:
            score = p['cats'][cat]
            cell_class = 'cat-scored' if score > 0 else 'cat-zero'
            cat_cells += f'<td class="{cell_class}">{score if score > 0 else "—"}</td>'

        leaderboard_rows += f'''
        <tr class="{rank_class}">
            <td class="rank-cell">{rank_display}</td>
            <td class="name-cell">{p["name"]}</td>
            <td class="total-cell">{p["total"]}</td>
            {cat_cells}
        </tr>'''

    # Build category header cells
    cat_headers = ''.join(f'<th class="cat-header"><span>{cat}</span></th>' for cat in categories)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Oscars Pool 2026 — Scores</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --base:    #1e1e2e;
    --mantle:  #181825;
    --crust:   #11111b;
    --surface0:#313244;
    --surface1:#45475a;
    --surface2:#585b70;
    --overlay0:#6c7086;
    --text:    #cdd6f4;
    --subtext0:#a6adc8;
    --subtext1:#bac2de;
    --gold:    #f9e2af;
    --green:   #a6e3a1;
    --blue:    #89dceb;
    --accent:  #cba6f7;
    --peach:   #fab387;
    --red:     #f38ba8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--base);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
  }}

  header {{
    background: var(--crust);
    padding: 20px;
    border-bottom: 1px solid var(--surface0);
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 8px 20px;
  }}
  header h1 {{
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: var(--gold);
  }}
  .back-link {{
    color: var(--accent);
    text-decoration: none;
    font-size: 0.82rem;
    font-weight: 500;
  }}
  .back-link:hover {{ text-decoration: underline; }}

  .scoreboard-wrap {{
    padding: 20px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    min-width: 700px;
  }}

  thead th {{
    background: var(--crust);
    padding: 10px 12px;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--subtext0);
    text-align: center;
    border-bottom: 2px solid var(--surface0);
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 1;
  }}
  thead th.cat-header {{
    font-size: 0.65rem;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    color: var(--overlay0);
  }}
  /* Rotate category headers so they don't blow out the width */
  thead th.cat-header span {{
    display: inline-block;
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    max-height: 120px;
    text-overflow: ellipsis;
    overflow: hidden;
    line-height: 1.2;
  }}
  thead th:first-child,
  thead th:nth-child(2),
  thead th:nth-child(3) {{
    text-align: left;
  }}

  tbody tr {{
    border-bottom: 1px solid var(--surface0);
    transition: background 0.1s;
  }}
  tbody tr:hover {{ background: rgba(203,166,247,0.04); }}
  tbody tr:last-child {{ border-bottom: none; }}

  td {{
    padding: 11px 12px;
    font-size: 0.85rem;
    text-align: center;
    vertical-align: middle;
  }}
  td:first-child, td:nth-child(2) {{ text-align: left; }}

  .rank-cell {{
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--subtext1);
    white-space: nowrap;
    min-width: 48px;
  }}
  .name-cell {{
    font-weight: 500;
    color: var(--text);
    white-space: nowrap;
  }}
  .total-cell {{
    font-weight: 700;
    font-size: 1rem;
    color: var(--gold);
    min-width: 56px;
  }}
  .cat-scored {{
    color: var(--green);
    font-weight: 500;
    font-size: 0.8rem;
  }}
  .cat-zero {{
    color: var(--surface2);
    font-size: 0.78rem;
  }}

  /* Top 3 row accents */
  tr.rank-1 {{ background: rgba(249,226,175,0.05); }}
  tr.rank-1 .rank-cell {{ color: var(--gold); }}
  tr.rank-2 {{ background: rgba(166,227,161,0.04); }}
  tr.rank-2 .rank-cell {{ color: var(--green); }}
  tr.rank-3 {{ background: rgba(137,220,235,0.03); }}
  tr.rank-3 .rank-cell {{ color: var(--blue); }}

  .note {{
    text-align: center;
    padding: 14px 20px;
    color: var(--overlay0);
    font-size: 0.78rem;
    font-style: italic;
    border-top: 1px solid var(--surface0);
  }}
</style>
</head>
<body>
<header>
  <h1>🏆 Scoreboard</h1>
  <a class="back-link" href="index.html">← Back to ballots</a>
</header>
<div class="scoreboard-wrap">
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Name</th>
        <th>Total</th>
        {cat_headers}
      </tr>
    </thead>
    <tbody>
      {leaderboard_rows}
    </tbody>
  </table>
</div>
<p class="note">Scores updated throughout the ceremony — refresh for latest standings</p>
</body>
</html>'''

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Done — {OUTPUT_HTML}")

if __name__ == '__main__':
    main()