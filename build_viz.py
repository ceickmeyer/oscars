import csv
import re
import json

INPUT_CSV = "oscars.csv"
OUTPUT_HTML = "viz.html"

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

    num_players = sum(1 for r in rows if r[2].strip())

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

    # Build vote data: per category, per nominee: {first, second, fun} counts
    viz_data = []
    for cat in cat_order:
        data = categories[cat]
        max_pts = data['max_pts']
        first_val = (max_pts * 2) // 3
        second_val = max_pts // 3
        nominee_data = []
        for nominee, idx in zip(data['nominees'], data['indices']):
            first = second = fun = 0
            for row in rows:
                if not row[2].strip():
                    continue
                cell = row[idx] if idx < len(row) else ''
                picks = parse_picks(cell, first_val, second_val)
                if 'first' in picks: first += 1
                if 'second' in picks: second += 1
                if 'fun' in picks: fun += 1
            if first + second + fun > 0:
                nominee_data.append({
                    'name': nominee,
                    'first': first,
                    'second': second,
                    'fun': fun,
                    'total': first + second + fun,
                    # weighted score: first=2pts, second=1pt, fun=0
                    'weight': first * 2 + second
                })
        # sort by weighted score desc
        nominee_data.sort(key=lambda x: x['weight'], reverse=True)
        viz_data.append({
            'cat': cat,
            'max_pts': max_pts,
            'nominees': nominee_data
        })

    viz_json = json.dumps(viz_data)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Oscars Pool 2026 — Visualizations</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
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
    --mauve:   #cba6f7;
    --peach:   #fab387;
    --red:     #f38ba8;
    --teal:    #94e2d5;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--crust);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    min-height: 100vh;
  }}

  /* Subtle film grain overlay */
  body::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
    opacity: 0.6;
  }}

  header {{
    position: relative;
    z-index: 1;
    background: var(--crust);
    border-bottom: 1px solid var(--surface0);
    padding: 24px 28px 20px;
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 8px 24px;
  }}
  header h1 {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 600;
    color: var(--gold);
    letter-spacing: 1px;
  }}
  header h1 em {{
    font-style: italic;
    color: var(--subtext0);
    font-size: 1.1rem;
    font-weight: 400;
    letter-spacing: 0;
  }}
  .nav-links {{
    display: flex;
    gap: 16px;
    margin-left: auto;
    align-items: center;
  }}
  .nav-links a {{
    color: var(--subtext0);
    text-decoration: none;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    transition: color 0.15s;
  }}
  .nav-links a:hover {{ color: var(--mauve); }}

  .player-count {{
    position: relative;
    z-index: 1;
    padding: 10px 28px;
    background: var(--mantle);
    border-bottom: 1px solid var(--surface0);
    font-size: 0.72rem;
    color: var(--overlay0);
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .player-count span {{ color: var(--gold); }}

  .legend {{
    position: relative;
    z-index: 1;
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    padding: 10px 28px;
    background: var(--mantle);
    border-bottom: 1px solid var(--surface0);
    font-size: 0.72rem;
    color: var(--subtext0);
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}
  .legend-item {{ display: flex; align-items: center; gap: 7px; }}
  .swatch {{
    width: 10px; height: 10px;
    border-radius: 2px;
    flex-shrink: 0;
  }}

  main {{
    position: relative;
    z-index: 1;
    padding: 28px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
  }}

  .cat-card {{
    background: var(--mantle);
    border: 1px solid var(--surface0);
    border-radius: 10px;
    overflow: hidden;
    opacity: 0;
    transform: translateY(12px);
    animation: fadeUp 0.4s ease forwards;
  }}

  @keyframes fadeUp {{
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  .cat-header {{
    padding: 12px 16px;
    background: var(--base);
    border-bottom: 1px solid var(--surface0);
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }}
  .cat-name {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: 0.3px;
  }}
  .cat-pts {{
    font-size: 0.68rem;
    color: var(--overlay0);
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}

  .nominees-list {{
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}

  .nominee-row {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .nominee-label {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }}
  .nominee-name {{
    font-size: 0.8rem;
    color: var(--subtext1);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 75%;
  }}
  .nominee-row.top-pick .nominee-name {{
    color: var(--text);
    font-weight: 500;
  }}
  .vote-counts {{
    font-size: 0.68rem;
    color: var(--overlay0);
    flex-shrink: 0;
    white-space: nowrap;
  }}
  .vote-counts .v-first {{ color: var(--gold); }}
  .vote-counts .v-second {{ color: var(--teal); }}
  .vote-counts .v-fun {{ color: var(--mauve); }}

  /* Stacked bar */
  .bar-track {{
    height: 8px;
    background: var(--surface0);
    border-radius: 4px;
    overflow: hidden;
    display: flex;
  }}
  .bar-seg {{
    height: 100%;
    transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    width: 0;
  }}
  .bar-seg.first  {{ background: var(--gold); }}
  .bar-seg.second {{ background: var(--teal); }}
  .bar-seg.fun    {{ background: var(--mauve); opacity: 0.6; }}

  /* No votes */
  .no-votes {{
    padding: 8px 0 4px;
    font-size: 0.72rem;
    color: var(--surface2);
    font-style: italic;
  }}

  @media (max-width: 500px) {{
    main {{ padding: 16px; grid-template-columns: 1fr; gap: 14px; }}
    header {{ padding: 18px 16px; }}
    .player-count, .legend {{ padding-left: 16px; padding-right: 16px; }}
  }}
</style>
</head>
<body>

<header>
  <h1>Oscars Pool <em>— the consensus</em></h1>
  <nav class="nav-links">
    <a href="index.html">Ballots</a>
    <a href="scores.html">Scores</a>
  </nav>
</header>
<div class="player-count">
  Showing picks from <span>{num_players}</span> players
</div>
<div class="legend">
  <div class="legend-item"><div class="swatch" style="background:var(--gold)"></div>1st pick (×2 weight)</div>
  <div class="legend-item"><div class="swatch" style="background:var(--teal)"></div>2nd pick</div>
  <div class="legend-item"><div class="swatch" style="background:var(--mauve);opacity:0.7"></div>For fun</div>
</div>

<main id="main"></main>

<script>
const NUM_PLAYERS = {num_players};
const DATA = {viz_json};

function render() {{
  const main = document.getElementById('main');

  DATA.forEach((cat, ci) => {{
    if (!cat.nominees.length) return;

    const maxWeight = cat.nominees[0].weight || 1;
    const card = document.createElement('div');
    card.className = 'cat-card';
    card.style.animationDelay = (ci * 0.04) + 's';

    let rows = '';
    cat.nominees.forEach((n, ni) => {{
      const totalVotes = n.first + n.second + n.fun;
      const pFirst  = (n.first  / NUM_PLAYERS) * 100;
      const pSecond = (n.second / NUM_PLAYERS) * 100;
      const pFun    = (n.fun    / NUM_PLAYERS) * 100;

      const countParts = [];
      if (n.first)  countParts.push(`<span class="v-first">★${{n.first}}</span>`);
      if (n.second) countParts.push(`<span class="v-second">◆${{n.second}}</span>`);
      if (n.fun)    countParts.push(`<span class="v-fun">♥${{n.fun}}</span>`);

      rows += `
        <div class="nominee-row ${{ni === 0 ? 'top-pick' : ''}}">
          <div class="nominee-label">
            <span class="nominee-name">${{n.name}}</span>
            <span class="vote-counts">${{countParts.join(' ')}}</span>
          </div>
          <div class="bar-track">
            <div class="bar-seg first"  data-w="${{pFirst}}"></div>
            <div class="bar-seg second" data-w="${{pSecond}}"></div>
            <div class="bar-seg fun"    data-w="${{pFun}}"></div>
          </div>
        </div>`;
    }});

    card.innerHTML = `
      <div class="cat-header">
        <span class="cat-name">${{cat.cat}}</span>
        <span class="cat-pts">${{cat.max_pts}} pts</span>
      </div>
      <div class="nominees-list">${{rows}}</div>`;

    main.appendChild(card);
  }});

  // Animate bars in after a short delay
  setTimeout(() => {{
    document.querySelectorAll('.bar-seg[data-w]').forEach(el => {{
      el.style.width = el.dataset.w + '%';
    }});
  }}, 120);
}}

render();
</script>
</body>
</html>'''

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Done — {OUTPUT_HTML}")

if __name__ == '__main__':
    main()
