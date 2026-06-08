"""
wc_engine.py — TrueLine World Cup 2026 prediction + auto-grading engine.

Builds Elo from full international match history, predicts all 2026 WC fixtures
(host-adjusted), auto-grades completed matches. Outputs JSON the static site fetches.

Model is CALIBRATED (Brier 0.150 across 2006-2022 World Cups), NOT a market edge.
Run daily during the tournament: refreshes ratings, re-predicts, re-grades automatically.

OUTPUT (writes to repo root so the GitHub Pages site can fetch them):
  - wc2026_predictions.json   (upcoming fixtures, 3-way probs, pick)
  - wc2026_ledger.json        (completed matches, predicted vs actual, hit, brier)
  - wc2026_summary.json       (headline stats for the ledger page)
  Also writes .csv copies for your own inspection.

USAGE:  python3 wc_engine.py
"""
import urllib.request
import json
from pathlib import Path
import pandas as pd
import numpy as np

# ---- config ----
HOSTS = {'United States', 'Canada', 'Mexico'}
K, HFA = 40, 65
RESULTS_URL = 'https://raw.githubusercontent.com/martj42/international_results/master/results.csv'
# where to write the JSON the site reads. "." = current dir (repo root). Change if needed.
OUT_DIR = Path('.')

def load():
    req = urllib.request.Request(RESULTS_URL, headers={'User-Agent': 'Mozilla/5.0'})
    from io import StringIO
    df = pd.read_csv(StringIO(urllib.request.urlopen(req, timeout=30).read().decode()))
    df['date'] = pd.to_datetime(df['date'])
    return df

def exp(ra, rb):
    return 1 / (1 + 10 ** ((rb - ra) / 400))

def build_elo(played):
    elo = {}
    for _, r in played.iterrows():
        h, a = r['home_team'], r['away_team']
        rh, ra = elo.get(h, 1500), elo.get(a, 1500)
        hfa = 0 if r['neutral'] else HFA
        eh = exp(rh + hfa, ra)
        sh = 1 if r['home_score'] > r['away_score'] else (0 if r['home_score'] < r['away_score'] else 0.5)
        mov = np.log(abs(r['home_score'] - r['away_score']) + 1)
        elo[h] = rh + K * mov * (sh - eh)
        elo[a] = ra + K * mov * ((1 - sh) - (1 - eh))
    return elo

def three_way(t1, t2, elo):
    e1, e2 = elo.get(t1, 1450), elo.get(t2, 1450)
    h1 = HFA if (t1 in HOSTS and t2 not in HOSTS) else 0
    h2 = HFA if (t2 in HOSTS and t1 not in HOSTS) else 0
    exp1 = exp(e1 + h1, e2 + h2)
    pdraw = 0.27 * (1 - abs(exp1 - 0.5) * 2) ** 0.6 + 0.04
    pdraw = min(max(pdraw, 0.05), 0.30)
    return (1 - pdraw) * exp1, pdraw, (1 - pdraw) * (1 - exp1), e1, e2

def predict_all(df, elo):
    fix = df[(df['home_score'].isna()) & (df['tournament'] == 'FIFA World Cup')].sort_values('date')
    rows = []
    for _, f in fix.iterrows():
        t1, t2 = f['home_team'], f['away_team']
        p1, pd_, p2, e1, e2 = three_way(t1, t2, elo)
        pick = max([('team1 win', p1), ('draw', pd_), ('team2 win', p2)], key=lambda x: x[1])
        rows.append({
            'date': str(f['date'].date()), 'team1': t1, 'team2': t2,
            'P_win': round(p1, 3), 'P_draw': round(pd_, 3), 'P_loss': round(p2, 3),
            'pick': pick[0], 'pick_prob': round(pick[1], 3),
            'host_game': bool(t1 in HOSTS or t2 in HOSTS)})
    return pd.DataFrame(rows)

def grade_ledger(df, elo):
    done = df[(df['tournament'] == 'FIFA World Cup') & (df['date'] >= '2026-06-11')
              & (df['home_score'].notna())].sort_values('date')
    rows = []
    for _, m in done.iterrows():
        t1, t2 = m['home_team'], m['away_team']
        p1, pd_, p2, _, _ = three_way(t1, t2, elo)
        if m['home_score'] > m['away_score']:
            actual = 'team1 win'
        elif m['home_score'] < m['away_score']:
            actual = 'team2 win'
        else:
            actual = 'draw'
        pick = max([('team1 win', p1), ('draw', pd_), ('team2 win', p2)], key=lambda x: x[1])[0]
        y = {'team1 win': [1, 0, 0], 'draw': [0, 1, 0], 'team2 win': [0, 0, 1]}[actual]
        brier = float(np.sum((np.array([p1, pd_, p2]) - np.array(y)) ** 2))
        rows.append({
            'date': str(m['date'].date()), 'team1': t1, 'team2': t2,
            'result': str(int(m['home_score'])) + '-' + str(int(m['away_score'])),
            'actual': actual, 'pick': pick, 'hit': bool(pick == actual),
            'brier': round(brier, 3),
            'P_win': round(p1, 3), 'P_draw': round(pd_, 3), 'P_loss': round(p2, 3)})
    return pd.DataFrame(rows)

def main():
    df = load()
    played = df.dropna(subset=['home_score', 'away_score']).sort_values('date')
    elo = build_elo(played)

    preds = predict_all(df, elo)
    preds.to_csv(OUT_DIR / 'wc2026_predictions.csv', index=False)
    (OUT_DIR / 'wc2026_predictions.json').write_text(preds.to_json(orient='records'))
    print(f'PREDICTIONS: {len(preds)} fixtures -> wc2026_predictions.json')

    ledger = grade_ledger(df, elo)
    ledger.to_csv(OUT_DIR / 'wc2026_ledger.csv', index=False)
    (OUT_DIR / 'wc2026_ledger.json').write_text(ledger.to_json(orient='records'))

    summary = {
        'matches_graded': int(len(ledger)),
        'pick_accuracy': round(float(ledger['hit'].mean()), 3) if len(ledger) else None,
        'mean_brier': round(float(ledger['brier'].mean()), 3) if len(ledger) else None,
        'updated': pd.Timestamp.now('UTC').strftime('%Y-%m-%d %H:%M UTC')}
    (OUT_DIR / 'wc2026_summary.json').write_text(json.dumps(summary))

    if len(ledger):
        print(f'LEDGER: {len(ledger)} graded | top-pick {summary["pick_accuracy"]:.0%} | Brier {summary["mean_brier"]:.3f}')
    else:
        print('LEDGER: empty (tournament starts June 11) — fills automatically as matches complete')
    print('JSON written:', [p.name for p in [OUT_DIR / 'wc2026_predictions.json',
          OUT_DIR / 'wc2026_ledger.json', OUT_DIR / 'wc2026_summary.json']])

if __name__ == '__main__':
    main()
