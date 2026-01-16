import streamlit as st
import pandas as pd
import requests
import io
import math
import json
import os
import time
from datetime import datetime, timedelta
from PIL import Image

# ML Libraries
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# --- 1. KONFIGURACJA UI ---
try:
    icon = Image.open("icon.png")
except:
    icon = "⚽"

st.set_page_config(page_title="TrafnyBetBot 3.2 FINAL", page_icon=icon, layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp {background-color: #1e1e1e; color: #e0e0e0;}
    
    /* Przyciski */
    div.stButton > button {
        width: 100%; border-radius: 8px; font-weight: bold; height: 3em; transition: 0.2s;
        background: linear-gradient(135deg, #8742f5 0%, #5e17eb 100%); border: none; color: white;
    }
    
    /* STYLE KOSZYK - Kolory Przycisków */
    div[data-testid="column"]:nth-of-type(1) .stButton > button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    div[data-testid="column"]:nth-of-type(2) .stButton > button { background: linear-gradient(135deg, #f09819 0%, #ff512f 100%); }
    div[data-testid="column"]:nth-of-type(3) .stButton > button { background: linear-gradient(135deg, #cb2d3e 0%, #ef473a 100%); box-shadow: 0 0 15px rgba(239, 71, 58, 0.6); border: 1px solid #ffcc00; }

    /* RAMKI */
    .watchlist-box { background-color: #2d2d2d; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #8742f5; }
    
    /* STYL MATEMATYKA (PERFECT LAYOUT) */
    .math-box { 
        background-color: #1b3a2b; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #2ecc71; 
        margin-bottom: 5px; 
        font-size: 0.9em;
        line-height: 1.6;
    }
    .math-row { display: flex; justify-content: space-between; border-bottom: 1px solid #2ecc7155; padding: 4px 0; }
    .math-row:last-child { border-bottom: none; }
    .math-header { font-weight: bold; color: #2ecc71; margin-bottom: 5px; text-transform: uppercase; margin-top: 15px; border-top: 2px solid #2ecc71; padding-top: 5px; }
    .math-header:first-child { margin-top: 0; border-top: none; }
    
    /* STYL ML */
    .ml-box { background-color: #2c0b0e; padding: 15px; border-radius: 8px; border: 1px solid #e74c3c; margin-bottom: 5px; height: 100%; }
    
    /* STYL DEJAVU */
    .dejavu-box { 
        background-color: #4a2c0b; 
        padding: 10px; 
        border-radius: 5px; 
        border: 1px solid #f39c12; 
        margin-bottom: 10px; 
        font-size: 0.9em;
    }
    .dejavu-item { margin-bottom: 4px; padding-bottom: 4px; border-bottom: 1px solid #f39c1255; }

    /* STATUSY */
    .match-future { color: #2ecc71; font-weight: bold; }
    .match-live { color: #f1c40f; font-weight: bold; animation: pulse 2s infinite; }
    .match-past { color: #e74c3c; font-weight: bold; text-decoration: line-through; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    
    [data-testid="stMetricValue"] {font-size: 1.0rem !important; color: #ffcc00;}
    </style>
    """, unsafe_allow_html=True)
# --- 2. MAKSYMALNA LISTA LIG DOSTĘPNA W DARMOWYM CSV ---
LIGI_KODY = {
    # WIELKA BRYTANIA
    "Anglia - Premier League": "E0", 
    "Anglia - Championship": "E1", 
    "Anglia - League 1": "E2", 
    "Anglia - League 2": "E3", 
    "Anglia - Conference": "EC",
    "Szkocja - Premiership": "SC0", 
    "Szkocja - Championship": "SC1", 
    "Szkocja - League 1": "SC2", 
    "Szkocja - League 2": "SC3",
    
    # EUROPA - TOP 5
    "Niemcy - Bundesliga": "D1", 
    "Niemcy - 2. Bundesliga": "D2",
    "Włochy - Serie A": "I1", 
    "Włochy - Serie B": "I2",
    "Hiszpania - La Liga": "SP1", 
    "Hiszpania - Segunda": "SP2",
    "Francja - Ligue 1": "F1", 
    "Francja - Ligue 2": "F2",
    
    # EUROPA - POZOSTAŁE
    "Holandia - Eredivisie": "N1", 
    "Belgia - Jupiler": "B1", 
    "Portugalia - Liga 1": "P1", 
    "Turcja - Super Lig": "T1", 
    "Grecja - Super League": "G1",
    
    # ŚWIAT I MNIEJSZE LIGI (Sekcja 'Extra')
    "Argentyna": "ARG", 
    "Austria": "AUT", 
    "Brazylia": "BRA", 
    "Chiny": "CHN",
    "Dania": "DNK", 
    "Finlandia": "FIN", 
    "Irlandia": "IRL", 
    "Japonia": "JPN",
    "Meksyk": "MEX", 
    "Norwegia": "NOR", 
    "Polska - Ekstraklasa": "POL", 
    "Rumunia": "ROU",
    "Rosja": "RUS", 
    "Szwecja": "SWE", 
    "Szwajcaria": "SWZ", 
    "USA - MLS": "USA"
}
USAGE_FILE = "api_usage.json"
if 'watchlist' not in st.session_state: st.session_state['watchlist'] = []
if 'df' not in st.session_state: st.session_state['df'] = None
if 'pobrane_mecze' not in st.session_state: st.session_state['pobrane_mecze'] = []
if 'last_api_call' not in st.session_state: st.session_state['last_api_call'] = 0 # ANTY-BAN TIMER
for k in ['ml_htft', 'ml_1x2', 'ml_btts', 'ml_ou15', 'ml_ou25', 'ml_corn', 'ml_card']:
    if k not in st.session_state: st.session_state[k] = None

# --- 3. HELPERY ---
def get_usage():
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(USAGE_FILE): return 0, today
    try:
        with open(USAGE_FILE, 'r') as f:
            data = json.load(f)
            return (data.get('count', 0), today) if data.get('date') == today else (0, today)
    except: return 0, today

def increment_usage(amount):
    current, today = get_usage()
    new_total = current + amount
    with open(USAGE_FILE, 'w') as f: json.dump({"date": today, "count": new_total}, f)
    return new_total

# --- 4. CSV LOADER ---
@st.cache_data(ttl=3600)
def pobierz_baze_csv(ile_lat=5):
    def clean_df(df, n, s):
        df.columns = [c.strip() for c in df.columns]
        df = df.rename(columns={'Home':'HomeTeam','Away':'AwayTeam','Res':'FTR','Result':'FTR'})
        cols = ['FTHG','FTAG','HC','AC','HY','AY']
        for c in cols:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype('int8')
            else: df[c] = 0
        if 'HomeTeam' in df.columns: df['HomeTeam'] = df['HomeTeam'].astype(str)
        if 'AwayTeam' in df.columns: df['AwayTeam'] = df['AwayTeam'].astype(str)
        df['Liga'] = n
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df['Miesiac'] = df['Date'].dt.month.fillna(0).astype('int8')
        return df

    curr_y = 25; start_y = curr_y - ile_lat
    sezony = [f"{i:02d}{i+1:02d}" for i in range(start_y, curr_y+1)]; sezony.reverse()
    wszystkie = []
    prog = st.progress(0); step=0; tot=len(LIGI_KODY)*(len(sezony)+1)
    
    for n, k in LIGI_KODY.items():
        try:
            r = requests.get(f"https://www.football-data.co.uk/new/{k}.csv", timeout=1)
            if r.status_code==200: df=pd.read_csv(io.StringIO(r.text)); df=clean_df(df,n,"Cur"); wszystkie.append(df)
        except: pass
        step+=1; prog.progress(min(step/tot,1.0))
        
    for s in sezony:
        for n, k in LIGI_KODY.items():
            try:
                r = requests.get(f"https://www.football-data.co.uk/mmz4281/{s}/{k}.csv", timeout=1)
                if r.status_code==200: df=pd.read_csv(io.StringIO(r.text)); df=clean_df(df,n,s); wszystkie.append(df)
            except: pass
        step+=1; prog.progress(min(step/tot,1.0))
    
    prog.empty()
    if wszystkie: return pd.concat(wszystkie, ignore_index=True).drop_duplicates()
    return pd.DataFrame()

# --- 5. SYSTEM ANTY-BAN (BUNKER MODE) ---
API_URL = "https://v3.football.api-sports.io"
DELAY_BETWEEN_CALLS = 2.0 # Sekundy przerwy między KAŻDYM zapytaniem

def wait_for_slot():
    """Strażnik czasu - zapobiega banom."""
    now = time.time()
    diff = now - st.session_state['last_api_call']
    if diff < DELAY_BETWEEN_CALLS:
        time.sleep(DELAY_BETWEEN_CALLS - diff)
    st.session_state['last_api_call'] = time.time()

@st.cache_data(ttl=3600, show_spinner=False)
def safe_api_request(url, headers, params):
    wait_for_slot() # <--- TUTAJ JEST OCHRONA
    try:
        return requests.get(url, headers=headers, params=params, timeout=10).json()
    except:
        return {}

def pobierz_mecze_zakres_api(api_key, dni_w_przod=3):
    headers = {"x-apisports-key": api_key}
    wszystkie = []
    increment_usage(dni_w_przod) 
    st.info(f"📡 Pobieranie... (Tryb BUNKIER aktywny)")

    for i in range(dni_w_przod):
        d = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            data = safe_api_request(f"{API_URL}/fixtures", headers, {"date": d})
            if 'response' in data:
                for item in data['response']:
                    dt_str = item['fixture']['date']
                    full_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    wszystkie.append({
                        'ID_Meczu': item['fixture']['id'], 
                        'ID_Home': item['teams']['home']['id'], 'ID_Away': item['teams']['away']['id'],
                        'Data': d, 
                        'Godzina': full_dt.strftime("%H:%M"), 
                        'Timestamp': full_dt.timestamp(), 
                        'Liga': item['league']['name'], 
                        'HomeTeam': item['teams']['home']['name'], 'AwayTeam': item['teams']['away']['name'],
                        'Label': f"{item['league']['name']} | {item['teams']['home']['name']} vs {item['teams']['away']['name']}",
                        'Miesiac': datetime.now().month
                    })
        except: pass

    wszystkie = sorted(wszystkie, key=lambda x: x['Timestamp'])
    return wszystkie

# --- FUNKCJE API (BEZ CACHE DEKORATORA, BO UZYWAJA SAFE_REQUEST Z CACHE) ---
def pobierz_sklady_api(api_key, fixture_id):
    headers = {"x-apisports-key": api_key}
    increment_usage(1)
    d = safe_api_request(f"{API_URL}/fixtures/lineups", headers, {"fixture": fixture_id})
    h, a = [], []
    if 'response' in d:
        for t in d['response']:
            xi = [p['player']['name'] for p in t['startXI']]
            if not h: h=xi
            else: a=xi
    return h, a

def analizuj_h2h_api(api_key, h_id, a_id):
    headers = {"x-apisports-key": api_key}
    increment_usage(1)
    d = safe_api_request(f"{API_URL}/fixtures/headtohead", headers, {"h2h": f"{h_id}-{a_id}"})
    hist=[]; p1=0; p2=0; tot=0
    found_types = []
    if 'response' in d:
        for m in d['response']:
            try:
                s = m['score']; dt = m['fixture']['date'][:10]
                ht_res = 'H' if s['halftime']['home'] > s['halftime']['away'] else ('A' if s['halftime']['away'] > s['halftime']['home'] else 'D')
                ft_res = 'H' if s['fulltime']['home'] > s['fulltime']['away'] else ('A' if s['fulltime']['away'] > s['fulltime']['home'] else 'D')
                l_type = None
                if ht_res == 'H' and ft_res == 'A': p1+=1; l_type="1/2"
                if ht_res == 'A' and ft_res == 'H': p2+=1; l_type="2/1"
                if l_type: found_types.append({'date': dt, 'type': l_type})
                hist.append(f"{dt}: HT {s['halftime']['home']}-{s['halftime']['away']} / FT {s['fulltime']['home']}-{s['fulltime']['away']}")
                tot+=1
            except: pass
    p1_pct = (p1/tot)*100 if tot else 0
    p2_pct = (p2/tot)*100 if tot else 0
    return hist, p1_pct, p2_pct, tot, found_types

def analizuj_forme_api(api_key, h_id, a_id):
    headers = {"x-apisports-key": api_key}
    increment_usage(2) 
    def check_team(tid):
        d = safe_api_request(f"{API_URL}/fixtures", headers, {"team": tid, "last": "15", "status": "FT"})
        s, c, cnt, l12, l21 = 0, 0, 0, 0, 0
        if 'response' in d:
            for m in d['response']:
                try:
                    sc = m['score']; g = m['goals']
                    if sc['halftime']['home'] is None: continue
                    cnt += 1
                    is_home = (m['teams']['home']['id'] == tid)
                    gh = g['home'] if is_home else g['away']
                    ga = g['away'] if is_home else g['home']
                    if gh: s+=gh
                    if ga: c+=ga
                    hh = sc['halftime']['home']; ha = sc['halftime']['away']
                    fh = sc['fulltime']['home']; fa = sc['fulltime']['away']
                    ht_l = 'H' if hh > ha else ('A' if ha > hh else 'D')
                    ft_l = 'H' if fh > fa else ('A' if fa > fh else 'D')
                    if is_home:
                        if ht_l == 'A' and ft_l == 'H': l21 += 1
                        if ht_l == 'H' and ft_l == 'A': l12 += 1
                    else:
                        if ht_l == 'H' and ft_l == 'A': l21 += 1
                        if ht_l == 'A' and ft_l == 'H': l12 += 1
                except: pass
        avg_s = s/cnt if cnt else 1.0; avg_c = c/cnt if cnt else 1.0
        return avg_s, avg_c, l12, l21, cnt

    h_s, h_c, h_12_cnt, h_21_cnt, h_tot = check_team(h_id)
    a_s, a_c, a_12_cnt, a_21_cnt, a_tot = check_team(a_id)
    
    h_12_pct = (h_12_cnt / h_tot * 100) if h_tot else 0
    h_21_pct = (h_21_cnt / h_tot * 100) if h_tot else 0
    a_12_pct = (a_12_cnt / a_tot * 100) if a_tot else 0
    a_21_pct = (a_21_cnt / a_tot * 100) if a_tot else 0
    
    pair_12 = (h_12_pct + a_12_pct) / 2
    pair_21 = (h_21_pct + a_21_pct) / 2

    ml_live_data = {'h_strength': (h_s + h_c), 'a_strength': (a_s + a_c)}

    xg_h = h_s * a_c * 1.1; xg_a = a_s * h_c
    def pois(k, l): return (math.exp(-l)*(l**k))/math.factorial(k)
    probs = {'1':0,'X':0,'2':0,'BTTS':0,'O15':0,'O25':0}
    for i in range(6):
        for j in range(6):
            p = pois(i, xg_h) * pois(j, xg_a)
            if i>j: probs['1']+=p
            elif i==j: probs['X']+=p
            else: probs['2']+=p
            if i>0 and j>0: probs['BTTS']+=p
            if i+j > 1.5: probs['O15']+=p
            if i+j > 2.5: probs['O25']+=p
            
    return {
        'pois': {k: v*100 for k,v in probs.items()}, 
        'live_stats': {
            'h_12_pct': h_12_pct, 'h_21_pct': h_21_pct,
            'a_12_pct': a_12_pct, 'a_21_pct': a_21_pct,
            'pair_12': pair_12, 'pair_21': pair_21
        },
        'ml_data': ml_live_data
    }

def analizuj_historia_api(api_key, h_id, a_id, h_name, a_name):
    headers = {"x-apisports-key": api_key}
    increment_usage(2) 
    prev_season = datetime.now().year - 1 
    curr_month = datetime.now().month
    messages = []
    
    def check_history(tid, team_name):
        d = safe_api_request(f"{API_URL}/fixtures", headers, {"team": tid, "season": prev_season, "status": "FT"})
        if 'response' in d:
            for m in d['response']:
                try:
                    dt_str = m['fixture']['date']
                    m_date = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    if abs(m_date.month - curr_month) <= 1:
                        sc = m['score']
                        if sc['halftime']['home'] is None: continue
                        hh, ha = sc['halftime']['home'], sc['halftime']['away']
                        fh, fa = sc['fulltime']['home'], sc['fulltime']['away']
                        ht_res = 'H' if hh > ha else ('A' if ha > hh else 'D')
                        ft_res = 'H' if fh > fa else ('A' if fa > fh else 'D')
                        l_type = ""
                        if ht_res == 'H' and ft_res == 'A': l_type = "1/2"
                        if ht_res == 'A' and ft_res == 'H': l_type = "2/1"
                        if l_type:
                            messages.append({'who': team_name, 'type': l_type, 'date': m_date.strftime('%Y-%m-%d')})
                except: pass
    check_history(h_id, h_name); check_history(a_id, a_name)
    return messages

# --- 6. ML & STATS ---
def analizuj_dejavu(df, h, a):
    if df is None: return []
    messages = []
    all_t = set(df['HomeTeam'])|set(df['AwayTeam'])
    rh = next((t for t in all_t if h.lower() in t.lower()), None)
    ra = next((t for t in all_t if a.lower() in t.lower()), None)
    curr_month = datetime.now().month
    def check_row(r, name):
        if r['Miesiac'] == curr_month:
            l_type = ""
            if r['HTR']=='H' and r['FTR']=='A': l_type = "1/2"
            if r['HTR']=='A' and r['FTR']=='H': l_type = "2/1"
            if l_type:
                return {'who': name, 'type': l_type, 'date': r['Date'].strftime('%d.%m.%Y')}
        return None
    if rh and ra:
        h2h = df[((df['HomeTeam']==rh)&(df['AwayTeam']==ra)) | ((df['HomeTeam']==ra)&(df['AwayTeam']==rh))]
        for i, r in h2h.iterrows():
            msg = check_row(r, "H2H (Para)")
            if msg: messages.append(msg)
    if rh:
        for i, r in df[(df['HomeTeam']==rh)|(df['AwayTeam']==rh)].iterrows():
            msg = check_row(r, rh)
            if msg: messages.append(msg)
    if ra:
        for i, r in df[(df['HomeTeam']==ra)|(df['AwayTeam']==ra)].iterrows():
            msg = check_row(r, ra)
            if msg: messages.append(msg)
    return messages

def calc_stat_lamaki(df, h, a):
    """CSV Stat"""
    if df is None: return {'h12':0,'h21':0,'a12':0,'a21':0,'pair_12':0,'pair_21':0}
    all_t = set(df['HomeTeam'])|set(df['AwayTeam'])
    rh = next((t for t in all_t if h.lower() in t.lower()), None)
    ra = next((t for t in all_t if a.lower() in t.lower()), None)
    if not rh or not ra: return {'h12':0,'h21':0,'a12':0,'a21':0,'pair_12':0,'pair_21':0}
    def get_pct(team):
        d = df[(df['HomeTeam']==team)|(df['AwayTeam']==team)]
        cnt, c12, c21 = 0,0,0
        for i, r in d.iterrows():
            cnt+=1
            if r['HomeTeam']==team:
                if r['HTR']=='H' and r['FTR']=='A': c12+=1
                if r['HTR']=='A' and r['FTR']=='H': c21+=1
            else:
                if r['HTR']=='H' and r['FTR']=='A': c12+=1
                if r['HTR']=='A' and r['FTR']=='H': c21+=1
        return (c12/cnt*100 if cnt else 0), (c21/cnt*100 if cnt else 0)
    h12, h21 = get_pct(rh); a12, a21 = get_pct(ra)
    p12 = (h12+a12)/2; p21 = (h21+a21)/2
    return {'h12':h12, 'h21':h21, 'a12':a12, 'a21':a21, 'pair_12':p12, 'pair_21':p21}

def get_team_lamaki_count(df, team_name):
    d = df[(df['HomeTeam'] == team_name) | (df['AwayTeam'] == team_name)]
    total = len(d); cnt = 0
    if total == 0: return 0, 0
    for i, r in d.iterrows():
        if (r['HTR'] == 'H' and r['FTR'] == 'A') or (r['HTR'] == 'A' and r['FTR'] == 'H'): cnt += 1
    return cnt, total

def train_generic(df, target_expr, feature_col):
    if df is None or df.empty: return None, None
    d = df.copy(); d['Target'] = target_expr(d)
    stats = {}
    for t in pd.concat([d['HomeTeam'], d['AwayTeam']]).unique():
        m = d[(d['HomeTeam']==t)|(d['AwayTeam']==t)]
        stats[t] = m[feature_col].mean() if not m.empty else 0.5
    d['H_S'] = d['HomeTeam'].map(stats).fillna(0); d['A_S'] = d['AwayTeam'].map(stats).fillna(0)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(d[['Miesiac','H_S','A_S']], d['Target'])
    return model, stats

def predict_generic(model, stats, m, h, a):
    if not model: return 0
    probs = model.predict_proba([[m, stats.get(h,0), stats.get(a,0)]])[0]
    return probs[1]*100 if 1 in model.classes_ else 0

def trenuj_htft(df):
    if df is None: return None, None
    d = df.copy()
    d['Target'] = d.apply(lambda r: 1 if r['HTR']=='H' and r['FTR']=='A' else (2 if r['HTR']=='A' and r['FTR']=='H' else 0), axis=1)
    ts = {}
    for t in pd.concat([d['HomeTeam'], d['AwayTeam']]).unique():
        m = d[(d['HomeTeam']==t)|(d['AwayTeam']==t)]
        ts[t] = (m['FTHG'].sum()+m['FTAG'].sum())/(len(m)+1) 
    d['H'] = d['HomeTeam'].map(ts).fillna(1); d['A'] = d['AwayTeam'].map(ts).fillna(1)
    model = RandomForestClassifier(n_estimators=100, class_weight='balanced', max_depth=10, random_state=42)
    model.fit(d[['Miesiac','H','A']], d['Target'])
    return model, ts

def predict_htft(model, stats, m, h, a, live_data=None):
    if not model: return "Brak modelu"
    if live_data:
        h_val = live_data['h_strength']
        a_val = live_data['a_strength']
    else:
        h_val = stats.get(h, 1)
        a_val = stats.get(a, 1)
    probs = model.predict_proba([[m, h_val, a_val]])[0]
    p1 = probs[list(model.classes_).index(1)]*100 if 1 in model.classes_ else 0
    p2 = probs[list(model.classes_).index(2)]*100 if 2 in model.classes_ else 0
    return f"1/2: {p1:.1f}% | 2/1: {p2:.1f}%"

def trenuj_1x2(df):
    if df is None: return None, None, None
    d = df.copy(); le = LabelEncoder(); d['Target'] = le.fit_transform(d['FTR'])
    ts = {}
    for t in pd.concat([d['HomeTeam'], d['AwayTeam']]).unique():
        mh=d[d['HomeTeam']==t]; ma=d[d['AwayTeam']==t]
        ts[t] = ((mh['FTHG']-mh['FTAG']).mean() + (ma['FTAG']-ma['FTHG']).mean())/2
    d['H'] = d['HomeTeam'].map(ts).fillna(0); d['A'] = d['AwayTeam'].map(ts).fillna(0)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(d[['Miesiac','H','A']], d['Target'])
    return model, ts, le

def predict_1x2(model, stats, le, m, h, a):
    if not model: return {}
    probs = model.predict_proba([[m, stats.get(h,0), stats.get(a,0)]])[0]
    return {c: probs[i]*100 for i,c in enumerate(le.classes_)}

def calc_math_csv(df, h, a):
    if df is None: return None
    all_t = set(df['HomeTeam'])|set(df['AwayTeam'])
    rh = next((t for t in all_t if h.lower() in t.lower()), None)
    ra = next((t for t in all_t if a.lower() in t.lower()), None)
    if not rh or not ra: return None
    try:
        mh=df[df['HomeTeam']==rh].tail(20); ma=df[df['AwayTeam']==ra].tail(20)
        avg_h = mh['FTHG'].mean() if not mh.empty else 1.2; avg_a = ma['FTAG'].mean() if not ma.empty else 1.0
        xg_h = avg_h * 1.1; xg_a = avg_a * 1.1
        def p(k, l): return (math.exp(-l)*(l**k))/math.factorial(k)
        probs = {'1':0,'X':0,'2':0,'BTTS':0,'O15':0,'O25':0}
        for i in range(6):
            for j in range(6):
                prob = p(i, xg_h)*p(j, xg_a)
                if i>j: probs['1']+=p
                elif i==j: probs['X']+=p
                else: probs['2']+=p
                if i>0 and j>0: probs['BTTS']+=p
                if i+j > 1.5: probs['O15']+=p
                if i+j > 2.5: probs['O25']+=p
        return {'pois': probs, 'corn': (mh['HC'].mean()+ma['AC'].mean()), 'card': (mh['HY'].mean()+ma['AY'].mean())}
    except: return None

def find_teams(df, h, a):
    all_t = set(df['HomeTeam'])|set(df['AwayTeam'])
    rh = next((t for t in all_t if h.lower() in t.lower()), None)
    ra = next((t for t in all_t if a.lower() in t.lower()), None)
    return rh, ra

# --- INTERFEJS SIDEBAR ---
with st.sidebar:
    try: st.image("icon.png", use_column_width=True)
    except: st.header("⚽")
    st.title("TrafnyBetBot 3.2 FINAL")
    api_key = st.text_input("Klucz API-Sports:", type="password")
    
    # STATUS API
    now = time.time()
    diff = now - st.session_state.get('last_api_call', 0)
    if diff < DELAY_BETWEEN_CALLS:
        st.markdown(f"🔴 **OSTYGANIE** ({DELAY_BETWEEN_CALLS - diff:.1f}s)")
    else:
        st.markdown("🟢 **GOTOWY**")

    st.markdown("---")
    
    if st.session_state['df'] is None:
        if st.button("📥 POBIERZ BAZĘ (Wszystkie Ligi)"):
            with st.spinner("Pobieranie 5 lat historii..."): 
                st.session_state['df'] = pobierz_baze_csv(5)
                st.rerun()
    else:
        st.success(f"Baza: {len(st.session_state['df'])} meczów")
        if st.button("🧠 TRENUJ WSZYSTKIE MODELE"):
            with st.spinner("Bot się uczy..."):
                df = st.session_state['df']
                m, s = trenuj_htft(df); st.session_state['ml_htft'] = {'m':m, 's':s}
                m, s, l = trenuj_1x2(df); st.session_state['ml_1x2'] = {'m':m, 's':s, 'l':l}
                m, s = train_generic(df, lambda d: ((d['FTHG']>0)&(d['FTAG']>0)).astype(int), 'FTHG'); st.session_state['ml_btts'] = {'m':m, 's':s}
                m, s = train_generic(df, lambda d: ((d['FTHG']+d['FTAG'])>1.5).astype(int), 'FTHG'); st.session_state['ml_ou15'] = {'m':m, 's':s}
                m, s = train_generic(df, lambda d: ((d['FTHG']+d['FTAG'])>2.5).astype(int), 'FTHG'); st.session_state['ml_ou25'] = {'m':m, 's':s}
                if 'HC' in df.columns: m, s = train_generic(df, lambda d: ((d['HC']+d['AC'])>9.5).astype(int), 'HC'); st.session_state['ml_corn'] = {'m':m, 's':s}
                if 'HY' in df.columns: m, s = train_generic(df, lambda d: ((d['HY']+d['AY'])>3.5).astype(int), 'HY'); st.session_state['ml_card'] = {'m':m, 's':s}
                st.success("✅ Modele Gotowe!")

    used, _ = get_usage()
    st.write(f"API: **{used}/100** pkt")
    
    st.markdown("---")
    st.caption("🚀 NOWOCZESNE (API+ML)")
    menu_api = ["1. RADAR (Skanuj)", "⭐ KOSZYK (Dual Core)", "🧠 1X2 (AI)", "🤝 BTTS (AI)", "⚽ GOLE (AI Over/Under)", "⛳ ROŻNE (AI)", "🟨 KARTKI (AI)"]
    st.caption("📚 KLASYCZNE (CSV Offline)")
    menu_csv = ["8. Schematy Ligowe", "9. Przeciwnik", "10. Łamak H2H (CSV+ML)", "11. H2H Kalendarz", "12. Gole xG (Calc+ML)", 
                "13. Remisy", "14. Dokładny Wynik", "15. Rożne (Calc+ML)", "16. Kartki (Calc+ML)", "17. BTTS (Calc+ML)", 
                "18. Pewniaki 1X2", "19. Słownik"]
    
    page = st.selectbox("Wybierz moduł:", menu_api + menu_csv)

# --- GŁÓWNA LOGIKA ---
df = st.session_state['df']

if page == "1. RADAR (Skanuj)":
    st.header("📡 Radar Meczowy (SAFE MODE)")
    if st.button("🚀 SKANUJ (3 pkt)"):
        if used>=100: st.error("Limit!"); st.stop()
        if not api_key: st.error("❌ WPISZ KLUCZ API!"); st.stop()
        with st.spinner("Pobieranie terminarza..."):
            st.session_state['pobrane_mecze'] = pobierz_mecze_zakres_api(api_key, 3); st.rerun()

    if st.session_state['pobrane_mecze']:
        st.write("---")
        statusy = st.multiselect("Filtruj status:", ["🟢 Przyszłe", "🟡 LIVE", "🔴 Koniec"], default=["🟢 Przyszłe", "🟡 LIVE"])
        mecze = st.session_state['pobrane_mecze']
        teraz = datetime.now().timestamp()
        
        c1, c2, c3, c4 = st.columns([1, 1, 3, 1])
        c1.write("**Data**"); c2.write("**Godzina**"); c3.write("**Mecz**"); c4.write("**Koszyk**")
        
        for m in mecze:
            ts = m['Timestamp']
            style_cls = "match-future"; status_icon = "🟢"; status_txt = "🟢 Przyszłe"
            if ts < teraz:
                if ts + (130*60) > teraz:
                    style_cls = "match-live"; status_icon = "🟡 LIVE"; status_txt = "🟡 LIVE"
                else:
                    style_cls = "match-past"; status_icon = "🔴 KONIEC"; status_txt = "🔴 Koniec"

            if status_txt in statusy:
                row1, row2, row3, row4 = st.columns([1, 1, 3, 1])
                with row1: st.write(m['Data'])
                with row2: st.markdown(f"<span class='{style_cls}'>{m['Godzina']} <br>{status_icon}</span>", unsafe_allow_html=True)
                with row3: st.write(m['Label'])
                with row4:
                    btn_key = f"btn_add_{m['ID_Meczu']}"
                    if st.button("⭐ Dodaj", key=btn_key):
                        if not any(x['Label']==m['Label'] for x in st.session_state['watchlist']):
                            st.session_state['watchlist'].append(m)
                            st.toast(f"Dodano: {m['Label']}")

elif page == "⭐ KOSZYK (Dual Core)":
    st.header("⭐ Centrum Decyzyjne (BUNKER MODE)")
    if not st.session_state['watchlist']: st.info("Koszyk pusty.")
    for m in st.session_state['watchlist']:
        st.markdown(f"<div class='watchlist-box'><b>{m['Label']}</b></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        k_s=f"s_{m['ID_Meczu']}"; k_p=f"p_{m['ID_Meczu']}"; k_pp=f"pp_{m['ID_Meczu']}"; act=None
        
        with c1: 
            if st.button("🔎 STANDARD (2 pkt)", key=k_s): act="STANDARD"
        with c2:
            if st.button("🧪 LIVE PRO (4 pkt)", key=k_p): act="PRO"
        with c3:
            if st.button("🔴 PRO+ (6 pkt)", key=k_pp): act="PRO+"
        
        if act:
            if not api_key: st.error("Brak klucza API!"); st.stop()
            if act=="STANDARD" and used>=98: st.error("Limit!"); st.stop()
            if act=="PRO" and used>=96: st.error("Limit!"); st.stop()
            if act=="PRO+" and used>=94: st.error("Limit!"); st.stop()
            
            # PASEK POSTĘPU DLA ZABICIA CZASU I INFORMACJI
            progress_text = "Analizuję... BUNKIER włączony."
            my_bar = st.progress(0, text=progress_text)
            
            # ETAP 1: H2H + Składy (Wspólne)
            h, p1, p2, tot, h2h_found = analizuj_h2h_api(api_key, m['ID_Home'], m['ID_Away'])
            my_bar.progress(30, text="Pobrano H2H...")
            sh, sa = pobierz_sklady_api(api_key, m['ID_Meczu'])
            my_bar.progress(50, text="Pobrano Składy...")
            
            res = {'h':h, 'p1':p1, 'p2':p2, 'tot':tot, 'sh':sh, 'sa':sa, 'type':act, 'dejavu': []}
            
            dejavu_csv = analizuj_dejavu(df, m['HomeTeam'], m['AwayTeam'])
            res['dejavu'].extend(dejavu_csv)
            for item in h2h_found:
                res['dejavu'].append({'who': 'H2H (Bezpośrednie)', 'type': item['type'], 'date': item['date']})

            if act=="STANDARD":
                if st.session_state['ml_htft']:
                    mod = st.session_state['ml_htft']
                    res['ml'] = predict_htft(mod['m'], mod['s'], m['Miesiac'], m['HomeTeam'], m['AwayTeam'])
                else: res['ml'] = "Brak modelu"
                mat = calc_math_csv(df, m['HomeTeam'], m['AwayTeam'])
                res['mat'] = mat if mat else {'1':0,'X':0,'2':0,'BTTS':0,'O15':0,'O25':0}
                res['stats'] = calc_stat_lamaki(df, m['HomeTeam'], m['AwayTeam'])
                res['src']="CSV Offline"; res['live']=None
                my_bar.progress(100, text="Gotowe!")
                
            else:
                # PRO / PRO+
                live = analizuj_forme_api(api_key, m['ID_Home'], m['ID_Away'])
                my_bar.progress(80, text="Pobrano Formę (Live ML)...")
                
                res['mat'] = live['pois']; res['src']="API Live Form"; 
                res['stats'] = {
                    'h12': live['live_stats']['h_12_pct'], 'h21': live['live_stats']['h_21_pct'],
                    'a12': live['live_stats']['a_12_pct'], 'a21': live['live_stats']['a_21_pct'],
                    'pair_12': live['live_stats']['pair_12'], 'pair_21': live['live_stats']['pair_21']
                }
                
                if st.session_state['ml_htft']:
                    mod = st.session_state['ml_htft']
                    res['ml'] = predict_htft(mod['m'], mod['s'], m['Miesiac'], m['HomeTeam'], m['AwayTeam'], live_data=live['ml_data'])
                    res['ml'] += " (API Data)"
                else: res['ml'] = "Brak modelu"
                
                if act == "PRO+":
                    my_bar.progress(90, text="Szukanie w historii API...")
                    dejavu_api = analizuj_historia_api(api_key, m['ID_Home'], m['ID_Away'], m['HomeTeam'], m['AwayTeam'])
                    res['dejavu'].extend(dejavu_api)
                
                my_bar.progress(100, text="Gotowe!")
            
            my_bar.empty()
            st.session_state[f"res_{m['ID_Meczu']}"] = res
        
        if f"res_{m['ID_Meczu']}" in st.session_state:
            r = st.session_state[f"res_{m['ID_Meczu']}"]
            
            # SEKCJA DÉJÀ VU
            if r.get('dejavu'):
                dv_h = [x for x in r['dejavu'] if x['who'] == m['HomeTeam'] or x['who'] == 'Gospodarz']
                dv_a = [x for x in r['dejavu'] if x['who'] == m['AwayTeam'] or x['who'] == 'Gość']
                dv_p = [x for x in r['dejavu'] if 'H2H' in x['who']]
                
                html_dv = "<div class='dejavu-box'><b>🔥 STREFA DÉJÀ VU:</b><br>"
                if dv_h: html_dv += f"<b>{m['HomeTeam']}:</b><br>" + "".join([f"<div class='dejavu-item'>{i['date']} - <b>{i['type']}</b></div>" for i in dv_h])
                if dv_a: html_dv += f"<b>{m['AwayTeam']}:</b><br>" + "".join([f"<div class='dejavu-item'>{i['date']} - <b>{i['type']}</b></div>" for i in dv_a])
                if dv_p: html_dv += f"<b>PARA (H2H):</b><br>" + "".join([f"<div class='dejavu-item'>{i['date']} - <b>{i['type']}</b></div>" for i in dv_p])
                html_dv += "</div>"
                st.markdown(html_dv, unsafe_allow_html=True)

            col_left, col_right = st.columns(2)
            with col_left:
                mat = r['mat']
                stats = r['stats']
                btts_yes = mat.get('BTTS', 0); btts_no = 100 - btts_yes
                ov15 = mat.get('O15', 0); un15 = 100 - ov15
                ov25 = mat.get('O25', 0); un25 = 100 - ov25
                p1 = mat.get('1', 0); px = mat.get('X', 0); p2 = mat.get('2', 0)

                html_math = f"""
                <div class='math-box'>
                    <div class='math-header'>🧮 MATEMATYKA ({r['src']})</div>
                    <div class='math-row'><span>BTTS:</span> <span>TAK <b>{btts_yes:.0f}%</b> | NIE {btts_no:.0f}%</span></div>
                    <div class='math-row'><span>1X2:</span> <span>1 <b>{p1:.0f}%</b> | X <b>{px:.0f}%</b> | 2 <b>{p2:.0f}%</b></span></div>
                    <div class='math-row'><span>1.5 Gola:</span> <span>OV <b>{ov15:.0f}%</b> | UN {un15:.0f}%</span></div>
                    <div class='math-row'><span>2.5 Gola:</span> <span>OV <b>{ov25:.0f}%</b> | UN {un25:.0f}%</span></div>
                    
                    <div class='math-header'>📉 ŁAMAKI (Statystyka % meczy)</div>
                    <div class='math-row'><b>{m['HomeTeam']}:</b></div>
                    <div class='math-row'><span>1/2: <b>{stats.get('h12',0):.1f}%</b></span> <span>2/1: <b>{stats.get('h21',0):.1f}%</b></span></div>
                    <div class='math-row'><b>{m['AwayTeam']}:</b></div>
                    <div class='math-row'><span>1/2: <b>{stats.get('a12',0):.1f}%</b></span> <span>2/1: <b>{stats.get('a21',0):.1f}%</b></span></div>
                    <div class='math-row'><b>🔥 PARA (Średnia):</b></div>
                    <div class='math-row'><span>1/2: <b>{stats.get('pair_12',0):.1f}%</b></span> <span>2/1: <b>{stats.get('pair_21',0):.1f}%</b></span></div>
                </div>
                """
                st.markdown(html_math, unsafe_allow_html=True)
            
            with col_right:
                src_ml = "API Live Data" if r['type'] in ["PRO", "PRO+"] else "Wzorce z CSV"
                st.markdown(f"<div class='ml-box'><b>🤖 ML ({src_ml})</b><br><br>{r['ml']}</div>", unsafe_allow_html=True)
            
            with st.expander("Składy i Szczegóły H2H"):
                if not r['sh']: st.write("Składy niedostępne.")
                else: st.write("Home:", r['sh']); st.write("Away:", r['sa'])
                st.write(r['h'])

# --- POZOSTAŁE ZAKŁADKI (BEZ ZMIAN) ---
elif page == "🧠 1X2 (AI)":
    st.header("🧠 1X2"); 
    if st.button("Analizuj 1X2"):
        if not st.session_state['ml_1x2']: st.error("Trenuj!"); st.stop()
        res=[]; mm=st.session_state['ml_1x2']
        pobrane = st.session_state['pobrane_mecze']
        if not pobrane: st.error("Najpierw Skanuj w Radarze!"); st.stop()
        for m in pobrane:
            p = predict_1x2(mm['m'], mm['s'], mm['l'], m['Miesiac'], m['HomeTeam'], m['AwayTeam'])
            mat = calc_math_csv(df, m['HomeTeam'], m['AwayTeam']); mp = mat['pois'] if mat else {}
            sig=""
            if p.get('H',0)>60 and mp.get('1',0)>55: sig="🔥 1"
            if p.get('A',0)>60 and mp.get('2',0)>55: sig="🔥 2"
            res.append({"Mecz": m['Label'], "AI 1": f"{p.get('H',0):.0f}%", "Mat 1": f"{mp.get('1',0):.0f}%", "Sygnał": sig})
        st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "🤝 BTTS (AI)":
    st.header("🤝 BTTS")
    if st.button("Analizuj BTTS"):
        if not st.session_state['ml_btts']: st.error("Trenuj!"); st.stop()
        res=[]; mm=st.session_state['ml_btts']
        pobrane = st.session_state['pobrane_mecze']
        if not pobrane: st.error("Najpierw Skanuj w Radarze!"); st.stop()
        for m in pobrane:
            ai = predict_generic(mm['m'], mm['s'], m['Miesiac'], m['HomeTeam'], m['AwayTeam'])
            mat = calc_math_csv(df, m['HomeTeam'], m['AwayTeam']); mp = mat['pois'].get('BTTS',0)*100 if mat else 0
            sig=""
            if ai>60 and mp>60: sig="🔥 TAK"
            if ai<40 and mp<40: sig="🧊 NIE"
            res.append({"Mecz": m['Label'], "AI Tak": f"{ai:.0f}%", "Mat Tak": f"{mp:.0f}%", "Sygnał": sig})
        st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "⚽ GOLE (AI Over/Under)":
    st.header("⚽ Linie Bramkowe (1.5 i 2.5)")
    if st.button("Analizuj Gole"):
        if not st.session_state['ml_ou25']: st.error("Trenuj!"); st.stop()
        res=[]; m15 = st.session_state['ml_ou15']; m25 = st.session_state['ml_ou25']
        pobrane = st.session_state['pobrane_mecze']
        if not pobrane: st.error("Najpierw Skanuj w Radarze!"); st.stop()
        for m in pobrane:
            ai15 = predict_generic(m15['m'], m15['s'], m['Miesiac'], m['HomeTeam'], m['AwayTeam'])
            ai25 = predict_generic(m25['m'], m25['s'], m['Miesiac'], m['HomeTeam'], m['AwayTeam'])
            mat = calc_math_csv(df, m['HomeTeam'], m['AwayTeam'])
            mp15 = mat['pois'].get('O15',0)*100 if mat else 0
            mp25 = mat['pois'].get('O25',0)*100 if mat else 0
            sig15 = "🔥 O1.5" if (ai15>70 and mp15>70) else ("🧊 U1.5" if (ai15<30 and mp15<30) else "-")
            sig25 = "🔥 O2.5" if (ai25>60 and mp25>60) else ("🧊 U2.5" if (ai25<35 and mp25<35) else "-")
            res.append({"Mecz": m['Label'], "AI O1.5": f"{ai15:.0f}%", "Mat O1.5": f"{mp15:.0f}%", "Sig 1.5": sig15,
                        "AI O2.5": f"{ai25:.0f}%", "Mat O2.5": f"{mp25:.0f}%", "Sig 2.5": sig25})
        st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "⛳ ROŻNE (AI)":
    st.header("⛳ Rożne > 9.5")
    if st.button("Analizuj Rożne"):
        if not st.session_state['ml_corn']: st.error("Trenuj!"); st.stop()
        res=[]; mm=st.session_state['ml_corn']
        pobrane = st.session_state['pobrane_mecze']
        if not pobrane: st.error("Najpierw Skanuj w Radarze!"); st.stop()
        for m in pobrane:
            ai = predict_generic(mm['m'], mm['s'], m['Miesiac'], m['HomeTeam'], m['AwayTeam'])
            mat = calc_math_csv(df, m['HomeTeam'], m['AwayTeam']); avg = mat['corn'] if mat else 0
            sig = "🔥 OVER" if (ai>65 and avg>10) else ""
            res.append({"Mecz": m['Label'], "AI >9.5": f"{ai:.0f}%", "Średnia": f"{avg:.1f}", "Sygnał": sig})
        st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "🟨 KARTKI (AI)":
    st.header("🟨 Kartki > 3.5")
    if st.button("Analizuj Kartki"):
        if not st.session_state['ml_card']: st.error("Trenuj!"); st.stop()
        res=[]; mm=st.session_state['ml_card']
        pobrane = st.session_state['pobrane_mecze']
        if not pobrane: st.error("Najpierw Skanuj w Radarze!"); st.stop()
        for m in pobrane:
            ai = predict_generic(mm['m'], mm['s'], m['Miesiac'], m['HomeTeam'], m['AwayTeam'])
            mat = calc_math_csv(df, m['HomeTeam'], m['AwayTeam']); avg = mat['card'] if mat else 0
            sig = "🔥 OVER" if (ai>65 and avg>4.5) else ""
            res.append({"Mecz": m['Label'], "AI >3.5": f"{ai:.0f}%", "Średnia": f"{avg:.1f}", "Sygnał": sig})
        st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "8. Schematy Ligowe":
    st.header("🛡️ Schematy Ligowe (Łamaki CSV)")
    if df is None: st.error("Pobierz bazę!"); st.stop()
    if st.button("Szukaj Królów Łamaków"):
        res = []
        for t in list(set(df['HomeTeam'])):
            d = df[(df['HomeTeam']==t)|(df['AwayTeam']==t)]
            if len(d)<10: continue
            cnt = len(d[((d['HTR']=='H')&(d['FTR']=='A'))|((d['HTR']=='A')&(d['FTR']=='H'))])
            if cnt>0: res.append({'Drużyna':t, 'Mecze':len(d), 'Łamaki':cnt})
        st.dataframe(pd.DataFrame(res).sort_values('Łamaki', ascending=False).head(20))

elif page == "9. Przeciwnik":
    st.header("⚔️ Szukanie Kata (Ofiary)")
    if df is None: st.error("Pobierz bazę!"); st.stop()
    my_team = st.text_input("Twoja drużyna:")
    if st.button("Szukaj") and my_team:
        res = []
        for opp in list(set(df['HomeTeam'])):
            if opp == my_team: continue
            m = df[((df['HomeTeam']==my_team)&(df['AwayTeam']==opp)) | ((df['HomeTeam']==opp)&(df['AwayTeam']==my_team))]
            wpadki = 0
            for i, r in m.iterrows():
                if r['HomeTeam']==my_team and r['HTR']=='H' and r['FTR']=='A': wpadki+=1
                if r['AwayTeam']==my_team and r['HTR']=='A' and r['FTR']=='H': wpadki+=1
            if wpadki > 0: res.append({'Rywal': opp, 'Wpadki': wpadki})
        st.dataframe(pd.DataFrame(res))

elif page == "10. Łamak H2H (CSV+ML)":
    st.header("🔄 Sprawdź H2H i Szansę na Łamaka")
    c1, c2 = st.columns(2)
    t1 = c1.text_input("Drużyna 1:"); t2 = c2.text_input("Drużyna 2:")
    if st.button("Sprawdź") and df is not None:
        rh, ra = find_teams(df, t1, t2)
        if rh and ra:
            if st.session_state['ml_htft']:
                mm = st.session_state['ml_htft']
                pred = predict_htft(mm['m'], mm['s'], datetime.now().month, rh, ra)
                st.warning(f"🤖 AI o Łamakach (Styl gry):\n{pred}")
            stat = calc_stat_lamaki(df, rh, ra)
            st.info(f"📊 MATEMATYKA (Częstotliwość występowania w CSV):\n1/2: {stat['h12']:.1f}% | 2/1: {stat['a21']:.1f}%")
            col_h, col_a = st.columns(2)
            c_h, t_h = get_team_lamaki_count(df, rh)
            c_a, t_a = get_team_lamaki_count(df, ra)
            col_h.metric(label=f"Łamaki {rh} (All Time)", value=f"{c_h} z {t_h} meczów")
            col_a.metric(label=f"Łamaki {ra} (All Time)", value=f"{c_a} z {t_a} meczów")
            m = df[((df['HomeTeam']==rh)&(df['AwayTeam']==ra)) | ((df['HomeTeam']==ra)&(df['AwayTeam']==rh))]
            st.write("📜 Historia H2H:")
            st.dataframe(m[['Date','HomeTeam','AwayTeam','HTR','FTR']])
        else: st.warning("Nie znaleziono w CSV.")

elif page == "11. H2H Kalendarz":
    st.header("📅 Kalendarz Łamaków")
    miesiac = st.slider("Miesiąc:", 1, 12, datetime.now().month)
    if st.button("Pokaż historię") and df is not None:
        m = df[df['Miesiac'] == miesiac]
        lamaki = m[((m['HTR']=='H')&(m['FTR']=='A'))|((m['HTR']=='A')&(m['FTR']=='H'))]
        st.dataframe(lamaki[['Date','HomeTeam','AwayTeam','HTR','FTR']])

elif page == "12. Gole xG (Calc+ML)":
    st.header("⚽ Kalkulator Goli")
    c1, c2 = st.columns(2); t1 = c1.text_input("Home:"); t2 = c2.text_input("Away:")
    if st.button("Licz") and df is not None:
        rh, ra = find_teams(df, t1, t2)
        if rh:
            res = calc_math_csv(df, rh, ra)
            ai15, ai25 = 0, 0
            if st.session_state['ml_ou15']:
                m15 = st.session_state['ml_ou15']; m25 = st.session_state['ml_ou25']
                ai15 = predict_generic(m15['m'], m15['s'], datetime.now().month, rh, ra)
                ai25 = predict_generic(m25['m'], m25['s'], datetime.now().month, rh, ra)
            if res:
                p=res['pois']
                st.info(f"📊 MAT (Poisson)\nO1.5: {p['O15']:.1f}% | O2.5: {p['O25']:.1f}%")
                st.warning(f"🤖 AI (ML)\nO1.5: {ai15:.1f}% | O2.5: {ai25:.1f}%")

elif page == "13. Remisy":
    st.header("⚖️ Szukanie Remisów")
    if st.button("Pokaż Ligi Remisowe") and df is not None:
        res = df.groupby('Liga')['FTR'].apply(lambda x: (x=='D').mean()).sort_values(ascending=False)
        st.write(res)

elif page == "14. Dokładny Wynik":
    st.header("🎯 Dokładny Wynik")
    c1, c2 = st.columns(2); t1 = c1.text_input("H:"); t2 = c2.text_input("A:")
    if st.button("Symuluj") and df is not None:
        rh, ra = find_teams(df, t1, t2)
        if rh:
            m = df[((df['HomeTeam']==rh)|(df['AwayTeam']==rh))].tail(10)
            avg_g = (m['FTHG'].sum()+m['FTAG'].sum())/len(m)
            st.info(f"Średnia goli w meczach {rh}: {avg_g:.1f}")

elif page == "15. Rożne (Calc+ML)":
    st.header("⛳ Rożne Statystyki")
    c1, c2 = st.columns(2); t1 = c1.text_input("H:"); t2 = c2.text_input("A:")
    if st.button("Licz Rożne") and df is not None:
        rh, ra = find_teams(df, t1, t2)
        if rh:
            res = calc_math_csv(df, rh, ra)
            ai = 0
            if st.session_state['ml_corn']:
                mm = st.session_state['ml_corn']
                ai = predict_generic(mm['m'], mm['s'], datetime.now().month, rh, ra)
            if res:
                st.info(f"📊 Średnia: {res['corn']:.1f}"); st.warning(f"🤖 AI >9.5: {ai:.1f}%")

elif page == "16. Kartki (Calc+ML)":
    st.header("🟨 Kartki Statystyki")
    c1, c2 = st.columns(2); t1 = c1.text_input("H:"); t2 = c2.text_input("A:")
    if st.button("Licz Kartki") and df is not None:
        rh, ra = find_teams(df, t1, t2)
        if rh:
            res = calc_math_csv(df, rh, ra)
            ai = 0
            if st.session_state['ml_card']:
                mm = st.session_state['ml_card']
                ai = predict_generic(mm['m'], mm['s'], datetime.now().month, rh, ra)
            if res:
                st.info(f"📊 Średnia: {res['card']:.1f}"); st.warning(f"🤖 AI >3.5: {ai:.1f}%")

elif page == "17. BTTS (Calc+ML)":
    st.header("🤝 BTTS Manual")
    c1, c2 = st.columns(2); t1 = c1.text_input("H:"); t2 = c2.text_input("A:")
    if st.button("Licz BTTS") and df is not None:
        rh, ra = find_teams(df, t1, t2)
        if rh:
            res = calc_math_csv(df, rh, ra)
            ai = 0
            if st.session_state['ml_btts']:
                mm = st.session_state['ml_btts']
                ai = predict_generic(mm['m'], mm['s'], datetime.now().month, rh, ra)
            if res:
                st.info(f"📊 MAT BTTS: {res['pois']['BTTS']:.1f}%"); st.warning(f"🤖 AI BTTS: {ai:.1f}%")

elif page == "18. Pewniaki 1X2":
    st.header("💎 Skaner Faworytów (CSV)")
    if st.button("Skanuj ostatnie 200 meczów") and df is not None:
        last = df.tail(200)
        faworyci = last[(last['FTHG'] > 2) & (last['FTAG'] == 0)]
        st.dataframe(faworyci[['Date','HomeTeam','AwayTeam','FTHG','FTAG']])

elif page == "19. Słownik":
    st.header("📖 Słownik Drużyn")
    q = st.text_input("Szukaj:")
    if df is not None and q:
        ts = sorted(list(set(df['HomeTeam'])|set(df['AwayTeam'])))
        st.write([t for t in ts if q.lower() in t.lower()])
