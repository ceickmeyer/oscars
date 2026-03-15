import csv
import re

INPUT_CSV = "oscars.csv"
OUTPUT_HTML = "index.html"

def obfuscate_name(name):
    parts = name.strip().split()
    if len(parts) >= 2:
        return parts[0] + ' ' + parts[-1][0] + '.'
    return name

def parse_picks(cell_value, first_val, second_val):
    picks = set()
    if not cell_value.strip():
        return picks
    parts = [p.strip() for p in cell_value.split(',')]
    for part in parts:
        if 'personal pick' in part.lower() or 'no points' in part.lower():
            picks.add('fun')
        else:
            m = re.search(r'(\d+)\s*points?', part, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                if val == first_val:
                    picks.add('first')
                elif val == second_val:
                    picks.add('second')
    return picks

def main():
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = list(next(reader))
        rows = list(reader)

    categories = {}
    cat_order = []
    for i, h in enumerate(headers[3:], 3):
        m = re.match(r'^(.+?) \((\d+) points possible\) \[(.+)\]$', h)
        if m:
            cat, max_pts, nominee = m.group(1), int(m.group(2)), m.group(3)
            if cat not in categories:
                categories[cat] = {'max_pts': max_pts, 'nominees': [], 'indices': []}
                cat_order.append(cat)
            categories[cat]['nominees'].append(nominee)
            categories[cat]['indices'].append(i)

    players = []
    for row in rows:
        if not row[2].strip():
            continue
        name = obfuscate_name(row[2].strip())
        picks_by_cat = {}
        for cat in cat_order:
            data = categories[cat]
            max_pts = data['max_pts']
            first_val = (max_pts * 2) // 3
            second_val = max_pts // 3
            nominee_picks = {}
            for nominee, idx in zip(data['nominees'], data['indices']):
                cell = row[idx] if idx < len(row) else ''
                pick_types = parse_picks(cell, first_val, second_val)
                if pick_types:
                    nominee_picks[nominee] = pick_types
            picks_by_cat[cat] = nominee_picks
        players.append({'name': name, 'picks': picks_by_cat})

    panels_html = ''
    picker_btns = ''

    for pi, player in enumerate(players):
        parts = player['name'].split()
        initials = ''.join(p[0].upper() for p in parts[:2])
        picker_btns += f'<button class="picker-btn" onclick="openBallot({pi})">'
        picker_btns += f'<span class="avatar">{initials}</span>'
        picker_btns += f'<span class="picker-name">{player["name"]}</span>'
        picker_btns += f'</button>\n'

        panel_content = ''
        for cat in cat_order:
            data = categories[cat]
            nominees = data['nominees']
            max_pts = data['max_pts']
            nominee_picks = player['picks'][cat]

            rows_html = ''
            for nominee in nominees:
                pick_types = nominee_picks.get(nominee, set())
                stars = ''
                if 'first' in pick_types:
                    stars += '<span class="star gold" title="1st pick (double points)">★</span>'
                if 'second' in pick_types:
                    stars += '<span class="star silver" title="2nd pick">◆</span>'
                if 'fun' in pick_types:
                    stars += '<span class="star blue" title="For fun — no points">♥</span>'

                picked_class = 'picked' if pick_types else ''
                rows_html += f'''
                <tr class="{picked_class}">
                    <td class="nominee-name">{nominee}</td>
                    <td class="stars">{stars}</td>
                </tr>'''

            panel_content += f'''
            <div class="category">
                <h3>{cat}<span class="pts-badge">{max_pts} pts</span></h3>
                <table><tbody>{rows_html}
                </tbody></table>
            </div>'''

        panels_html += f'''
        <div class="ballot-panel" id="panel-{pi}" hidden>
            <div class="ballot-header">
                <button class="back-btn" onclick="closeBallot()">← All ballots</button>
                <span class="ballot-name">{player["name"]}</span>
            </div>
            <div class="grid">{panel_content}
            </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Oscars Pool 2026</title>
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
    --silver:  #a6e3a1;
    --blue:    #89dceb;
    --accent:  #cba6f7;
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
  }}
  header h1 {{
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: var(--gold);
  }}
  header p {{
    color: var(--overlay0);
    font-size: 0.78rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 4px;
  }}
  .header-note {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px 16px;
    margin-top: 12px;
  }}
  .form-link {{
    display: inline-block;
    background: var(--accent);
    color: var(--crust);
    text-decoration: none;
    font-size: 0.82rem;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 6px;
    white-space: nowrap;
    transition: opacity 0.15s;
  }}
  .form-link:hover {{ opacity: 0.85; }}
  .scores-link {{
    display: inline-block;
    background: transparent;
    color: var(--gold);
    border: 1px solid var(--gold);
    text-decoration: none;
    font-size: 0.82rem;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 6px;
    white-space: nowrap;
    transition: opacity 0.15s;
  }}
  .scores-link:hover {{ opacity: 0.75; }}
  .update-note {{
    color: var(--overlay0);
    font-size: 0.78rem;
    font-style: italic;
  }}

  .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px 20px;
    padding: 10px 20px;
    background: var(--mantle);
    border-bottom: 1px solid var(--surface0);
    font-size: 0.8rem;
    color: var(--subtext0);
  }}
  .legend span {{ display: flex; align-items: center; gap: 6px; }}

  /* ── Picker ── */
  #picker {{
    padding: 28px 20px;
  }}
  .picker-label {{
    font-size: 0.78rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--overlay0);
    margin-bottom: 16px;
  }}
  .picker-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 12px;
  }}
  .picker-btn {{
    background: var(--mantle);
    border: 1px solid var(--surface0);
    border-radius: 10px;
    padding: 18px 12px 14px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    transition: border-color 0.15s, background 0.15s, transform 0.12s;
    -webkit-tap-highlight-color: transparent;
  }}
  .picker-btn:hover {{
    border-color: var(--accent);
    background: rgba(203,166,247,0.07);
    transform: translateY(-2px);
  }}
  .picker-btn:active {{ transform: scale(0.97); }}
  .avatar {{
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: var(--surface0);
    border: 2px solid var(--surface1);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent);
    flex-shrink: 0;
  }}
  .picker-name {{
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text);
    text-align: center;
    line-height: 1.3;
    word-break: break-word;
  }}

  /* ── Ballot panel ── */
  .ballot-panel[hidden] {{ display: none; }}

  .ballot-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 20px;
    background: var(--mantle);
    border-bottom: 1px solid var(--surface0);
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  .back-btn {{
    background: transparent;
    border: 1px solid var(--surface1);
    color: var(--subtext0);
    padding: 7px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.82rem;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    transition: color 0.15s, border-color 0.15s;
    white-space: nowrap;
    -webkit-tap-highlight-color: transparent;
    flex-shrink: 0;
  }}
  .back-btn:hover {{ color: var(--text); border-color: var(--accent); }}
  .ballot-name {{
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    color: var(--gold);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}

  /* ── Category grid ── */
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 14px;
    padding: 20px;
  }}
  .category {{
    background: var(--mantle);
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--surface0);
  }}
  .category h3 {{
    padding: 10px 14px;
    background: var(--crust);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.5px;
    color: var(--subtext1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--surface0);
    text-transform: uppercase;
  }}
  .pts-badge {{
    font-size: 0.7rem;
    color: var(--overlay0);
    font-weight: 400;
    letter-spacing: 0;
    text-transform: none;
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  tr {{ border-bottom: 1px solid var(--surface0); }}
  tr:last-child {{ border-bottom: none; }}
  tr.picked {{ background: rgba(203, 166, 247, 0.05); }}
  td {{ padding: 10px 14px; vertical-align: middle; }}
  .nominee-name {{
    font-size: 0.85rem;
    color: var(--overlay0);
    line-height: 1.3;
  }}
  tr.picked .nominee-name {{ color: var(--text); }}
  .stars {{ text-align: right; white-space: nowrap; width: 1%; padding-left: 8px; }}
  .star {{
    font-size: 1.05rem;
    display: inline-block;
    margin-left: 3px;
    line-height: 1;
  }}
  .star.gold   {{ color: var(--gold);   filter: drop-shadow(0 0 4px rgba(249,226,175,0.5)); }}
  .star.silver {{ color: var(--silver); filter: drop-shadow(0 0 4px rgba(166,227,161,0.4)); }}
  .star.blue   {{ color: var(--blue);   filter: drop-shadow(0 0 4px rgba(137,220,235,0.4)); }}

  @media (max-width: 500px) {{
    .grid {{ grid-template-columns: 1fr; padding: 14px; }}
    .picker-grid {{ grid-template-columns: repeat(3, 1fr); gap: 10px; }}
    #picker {{ padding: 20px 16px; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Oscars Pool 2026</h1>
  <p>Follow along &amp; track your picks</p>
  <div class="header-note">
    <a class="form-link" href="https://docs.google.com/forms/d/e/1FAIpQLScOZqyB_FIuUnetQZt8S18rlAFoWXOlg4kZlmumui9VffuLDA/viewform?usp=sharing&ouid=107949562553462332189" target="_blank" rel="noopener">
      🎬 Submit your ballot
    </a>
    <a class="scores-link" href="scores.html">🏆 Scoreboard</a>
    <a class="scores-link" href="viz.html">📊 Consensus</a>
    <span class="update-note">Ballots will be updated before the ceremony</span>
  </div>
</header>
<div class="legend">
  <span><span class="star gold">★</span> 1st pick — double points</span>
  <span><span class="star silver">◆</span> 2nd pick</span>
  <span><span class="star blue">♥</span> For fun — no points</span>
</div>

<div id="picker">
  <p class="picker-label">Whose ballot do you want to see?</p>
  <div class="picker-grid">
{picker_btns}  </div>
</div>

{panels_html}

<script>
function openBallot(idx) {{
  document.getElementById('picker').hidden = true;
  document.getElementById('panel-' + idx).hidden = false;
  window.scrollTo(0, 0);
}}
function closeBallot() {{
  document.querySelectorAll('.ballot-panel').forEach(p => p.hidden = true);
  document.getElementById('picker').hidden = false;
  window.scrollTo(0, 0);
}}
</script>
</body>
</html>'''

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Done — {OUTPUT_HTML}")

if __name__ == '__main__':
    main()