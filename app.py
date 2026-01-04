import streamlit as st
import pandas as pd
import requests
import io
import math
from datetime import datetime
from PIL import Image

# --- 1. KONFIGURACJA STRONY ---
try:
    icon = Image.open("icon.png")
except:
    icon = "⚽"

st.set_page_config(
    page_title="TrafnyBetBot Pro",
    page_icon=icon,
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. CSS (WERSJA BEZPIECZNA - PRZYWRACA STANDARDOWY NAGŁÓWEK) ---
st.markdown("""
    <style>
    /* 1. Resetujemy ustawienia nagłówka - przywracamy go w całości */
    header {
        visibility: visible !important;
        background-color: transparent !important;
    }

    /* 2. Zostawiamy tylko ukrycie stopki "Made with Streamlit" */
    footer {
        visibility: hidden !important;
    }
    
    /* 3. Kolorowanie strzałki (jeśli system pozwoli, ale bez ukrywania reszty) */
    [data-testid="stSidebarCollapsedControl"] {
        color: #8742f5 !important;
    }

    /* 4. Ciemny motyw tła */
    .stApp {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    
    /* 5. Stylizacja Przycisków (Twój styl) */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #8742f5 0%, #5e17eb 100%);
        color: white;
        border: none;
        border-radius: 10px;
        height: 3.5em;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(135, 66, 245, 0.3);
    }
    
    /* 6. Inputy */
    [data-testid="stTextInput"] input, [data-testid="stSelectbox"] > div > div {
        background-color: #2d2d2d !important; 
        color: white !important; 
        border: 1px solid #444;
    }
    
    /* 7. Tabele */
    [data-testid="stDataFrame"] {
        border: 1px solid #333; 
        border-radius: 8px;
    }
    
    /* 8. Logo w sidebarze */
    [data-testid="stSidebar"] img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* 9. Marginesy Mobile - Zapewniamy miejsce na standardowy nagłówek */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 4rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
# --- 3. PEŁNA LISTA LIG ---
LIGI_KODY = {
    # ANGLIA
    "Anglia - Premier League": "E0", "Anglia - Championship": "E1",
    "Anglia - League 1": "E2", "Anglia - League 2": "E3", "Anglia - Conference": "EC",
    # SZKOCJA
    "Szkocja - Premiership": "SC0", "Szkocja - Div 1": "SC1", "Szkocja - Div 2": "SC2", "Szkocja - Div 3": "SC3",
    # NIEMCY
    "Niemcy - Bundesliga 1": "D1", "Niemcy - Bundesliga 2": "D2", "Niemcy - 3. Liga": "D3",
    # WŁOCHY
    "Włochy - Serie A": "I1", "Włochy - Serie B": "I2",
    # HISZPANIA
    "Hiszpania - La Liga": "SP1", "Hiszpania - Segunda": "SP2",
    # FRANCJA
    "Francja - Ligue 1": "F1", "Francja - Ligue 2": "F2",
    # EUROPA
    "Holandia": "N1", "Belgia": "B1", "Portugalia": "P1", "Turcja": "T1", "Grecja": "G1",
    # ŚWIAT
    "Polska - Ekstraklasa": "POL", "Austria - Bundesliga": "AUT", "Szwajcaria - Super League": "SWZ",
    "Szwecja - Allsvenskan": "SWE", "Norwegia - Eliteserien": "NOR", "Dania - Superliga": "DNK",
    "Finlandia - Veikkausliiga": "FIN", "Irlandia - Premier": "IRL", "Rumunia - Liga 1": "ROU",
    "Rosja - Premier League": "RUS", "USA - MLS": "USA", "Meksyk - Liga MX": "MEX",
    "Brazylia - Serie A": "BRA", "Argentyna - Liga Pro": "ARG", "Chiny - Super League": "CHN", "Japonia - J-League": "JPN"
}
# --- FUNKCJE (OPTIMIZED) ---
def clean_df(df, n, s):
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={'Home':'HomeTeam','Away':'AwayTeam','Res':'FTR','Result':'FTR'})
    req=['Date','HomeTeam','AwayTeam','HTR','FTR','FTHG','FTAG']
    opt=['HC','AC','HY','AY','HR','AR']
    
    for c in opt: 
        if c not in df.columns: df[c] = 0
        else: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype('int8')
    if 'FTHG' in df.columns: df['FTHG'] = pd.to_numeric(df['FTHG'], errors='coerce').fillna(0).astype('int8')
    if 'FTAG' in df.columns: df['FTAG'] = pd.to_numeric(df['FTAG'], errors='coerce').fillna(0).astype('int8')
    if 'FTR' not in df.columns: df['FTR']='D'
    
    if 'HomeTeam' in df.columns: df['HomeTeam'] = df['HomeTeam'].astype(str)
    if 'AwayTeam' in df.columns: df['AwayTeam'] = df['AwayTeam'].astype(str)

    if set(['HomeTeam','AwayTeam']).issubset(df.columns):
        df['Liga'] = n
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df['Rok'] = df['Date'].dt.year.fillna(0).astype('int16')
            df['Miesiac'] = df['Date'].dt.month.fillna(0).astype('int8')
        cols = list(set(req+opt+['Liga','Rok','Miesiac']) & set(df.columns))
        return df[cols]
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def pobierz_dane(ile_lat):
    curr_y = 25; start_y = curr_y - ile_lat
    sezony = [f"{i:02d}{i+1:02d}" for i in range(start_y, curr_y+1)]; sezony.reverse()
    wszystkie = []
    
    for n, k in LIGI_KODY.items():
        try:
            r = requests.get(f"https://www.football-data.co.uk/new/{k}.csv", timeout=1)
            if r.status_code==200:
                df = pd.read_csv(io.StringIO(r.text)); df = clean_df(df, n, "Current")
                wszystkie.append(df)
        except: pass
    
    if ile_lat > 0:
        for s in sezony:
            for n, k in LIGI_KODY.items():
                try:
                    r = requests.get(f"https://www.football-data.co.uk/mmz4281/{s}/{k}.csv", timeout=1)
                    if r.status_code==200:
                        df = pd.read_csv(io.StringIO(r.text)); df = clean_df(df, n, s)
                        wszystkie.append(df)
                except: pass
    
    if wszystkie:
        final = pd.concat(wszystkie, ignore_index=True).drop_duplicates()
        if 'Date' in final.columns:
            final['Date'] = pd.to_datetime(final['Date'], dayfirst=True, errors='coerce')
            final = final.sort_values('Date')
        return final
    return pd.DataFrame()

def find_teams(df, h, a):
    if df.empty: return None, None
    all_t = set(df['HomeTeam'])|set(df['AwayTeam'])
    rh = next((t for t in all_t if h.lower() in t.lower()), None)
    ra = next((t for t in all_t if a.lower() in t.lower()), None)
    return rh, ra

# --- SILNIK ANALITYCZNY (PROFESSIONAL) ---
def calculate_metrics(df, rh, ra):
    try:
        match_row = df[df['HomeTeam'] == rh].iloc[-1] if not df[df['HomeTeam'] == rh].empty else None
        if match_row is None: return None
        
        liga = match_row['Liga']
        df_league = df[df['Liga'] == liga].tail(500)
        
        avg_hg = df_league['FTHG'].mean() if not df_league.empty else 1.35
        avg_ag = df_league['FTAG'].mean() if not df_league.empty else 1.15
        
        mh = df[df['HomeTeam'] == rh].tail(20)
        ma = df[df['AwayTeam'] == ra].tail(20)
        
        if mh.empty or ma.empty: return None
        
        h_att = (mh['FTHG'].mean() / avg_hg)
        h_def = (mh['FTAG'].mean() / avg_ag)
        a_att = (ma['FTAG'].mean() / avg_ag)
        a_def = (ma['FTHG'].mean() / avg_hg)
        
        xg_h = avg_hg * h_att * a_def
        xg_a = avg_ag * a_att * h_def
        
        return {'xg_h': xg_h, 'xg_a': xg_a}
    except: return None

def poisson_probability(xg_h, xg_a):
    def poisson(k, lam): return (math.exp(-lam) * (lam**k)) / math.factorial(k)
    probs = {'1': 0, 'X': 0, '2': 0, 'O1.5': 0, 'O2.5': 0, 'BTTS': 0}
    prob_matrix = []
    for i in range(6):
        for j in range(6):
            p = poisson(i, xg_h) * poisson(j, xg_a)
            if i > j: probs['1'] += p
            elif i == j: probs['X'] += p
            else: probs['2'] += p
            if i + j > 1.5: probs['O1.5'] += p
            if i + j > 2.5: probs['O2.5'] += p
            if i > 0 and j > 0: probs['BTTS'] += p
            if p * 100 > 3.0: prob_matrix.append((f"{i}:{j}", p*100))
    prob_matrix.sort(key=lambda x:x[1], reverse=True)
    return probs, prob_matrix

# --- SIDEBAR (MENU) ---
with st.sidebar:
    try: st.image("icon.png", width=120)
    except: st.title("TrafnyBetBot")
    st.markdown("---")
    
    st.header("NARZĘDZIA")
    menu_options = [
        "1. Schematy", "2. Przeciwnik", "3. Łamak 1/2", "4. H2H Kalendarz", 
        "5. Gole (xG)", "6. Remisy", "7. Dokładny Wynik", "8. Rożne", "9. Kartki", 
        "10. BTTS", "11. Perełki (Value)", "12. Słownik"
    ]
    selected_page = st.selectbox("Wybierz opcję:", menu_options, label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### Baza Danych")
    opcje = {"1 rok (Szybko)":1, "5 lat":5, "10 lat":10, "15 lat":15}
    wybor = st.selectbox("Zakres:", list(opcje.keys()), index=0)
    
    if st.button("POBIERZ BAZĘ"):
        with st.spinner("Aktualizacja..."):
            st.session_state['df'] = pobierz_dane(opcje[wybor])
        st.success(f"Gotowe! Mecze: {len(st.session_state['df'])}")

# --- MAIN UI ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try: st.image("icon.png", width=50)
    except: st.write("⚽")
with col_title:
    st.title(selected_page)

if 'df' not in st.session_state or st.session_state['df'].empty:
    st.info("👈 Kliknij strzałkę '>' w lewym górnym rogu i pobierz bazę danych.")
    st.stop()

df = st.session_state['df']

# --- ZAKŁADKI ---

if selected_page == "1. Schematy":
    if st.button("Skanuj Trendy"):
        teams = set(df['HomeTeam'])|set(df['AwayTeam']); res=[]
        for t in teams:
            d = df[(df['HomeTeam']==t)|(df['AwayTeam']==t)]
            if len(d)<5: continue
            hard = len(d[((d['HTR']=='H')&(d['FTR']=='A'))|((d['HTR']=='A')&(d['FTR']=='H'))])
            if hard>0: res.append({'Drużyna':t, 'Mecze':len(d), 'Łamaki':hard})
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("👑 Królowie Łamaków")
            if res: st.dataframe(pd.DataFrame(res).sort_values('Łamaki', ascending=False).head(15), use_container_width=True)
        with c2:
            st.subheader("🔥 Serie H2H")
            p = df[((df['HTR']=='H')&(df['FTR']=='A'))|((df['HTR']=='A')&(df['FTR']=='H'))]
            if not p.empty:
                cnt = p.groupby(['HomeTeam','AwayTeam']).size().reset_index(name='Ilość')
                st.dataframe(cnt[cnt['Ilość']>=2].sort_values('Ilość', ascending=False), use_container_width=True)

elif selected_page == "2. Przeciwnik":
    mt = st.text_input("Gospodarz (Twoja drużyna):")
    if st.button("Szukaj Ofiary") and mt:
        rh, _ = find_teams(df, mt, "x")
        if rh:
            cand=[]
            for op in (set(df['HomeTeam'])|set(df['AwayTeam'])):
                if op==rh: continue
                ma=df[df['AwayTeam']==op]
                choke=len(ma[(ma['HTR']=='A')&(ma['FTR']=='H')])
                if choke>0: cand.append({'Rywal':op, 'Wpadki (Łamak)':choke})
            if cand: st.dataframe(pd.DataFrame(cand).sort_values('Wpadki (Łamak)',ascending=False).head(20), use_container_width=True)
            else: st.info("Brak kandydatów.")

elif selected_page == "3. Łamak 1/2":
    c1, c2 = st.columns(2)
    h = c1.text_input("Gosp:", key="t3h"); a = c2.text_input("Gość:", key="t3a")
    if st.button("Analiza HT/FT"):
        rh, ra = find_teams(df, h, a)
        if rh and ra:
            h_all = df[(df['HomeTeam']==rh)|(df['AwayTeam']==rh)]
            h_lam = len(h_all[((h_all['HTR']=='H')&(h_all['FTR']=='A'))|((h_all['HTR']=='A')&(h_all['FTR']=='H'))])
            mh = df[df['HomeTeam']==rh]; ma = df[df['AwayTeam']==ra]
            h_lead = len(mh[mh['HTR']=='H']); h_choke = len(mh[(mh['HTR']=='H')&(mh['FTR']=='A')])
            h_pct = (h_choke/h_lead*100) if h_lead > 0 else 0
            a_trail = len(ma[ma['HTR']=='H']); a_come = len(ma[(ma['HTR']=='H')&(ma['FTR']=='A')])
            a_pct = (a_come/a_trail*100) if a_trail > 0 else 0
            avg_prob = (h_pct + a_pct) / 2
            st.metric("Szansa Matematyczna", f"{avg_prob:.1f}%")
            st.write(f"**{rh} (Dom):** Przegrał z prowadzenia {h_choke} razy ({h_pct:.1f}%)")
            st.write(f"**{ra} (Wyjazd):** Wygrał z przegranej {a_come} razy ({a_pct:.1f}%)")

elif selected_page == "4. H2H Kalendarz":
    m = st.slider("Miesiąc:", 1, 12, datetime.now().month)
    if st.button("Szukaj Historii"):
        lam = df[(((df['HTR']=='H')&(df['FTR']=='A'))|((df['HTR']=='A')&(df['FTR']=='H'))) & (df['Miesiac']==m)]
        if not lam.empty:
            pairs = lam.groupby(['HomeTeam','AwayTeam'])
            res = []
            for (h_t, a_t), g in pairs:
                yrs = sorted(g['Rok'].unique(), reverse=True)
                lata_str = ", ".join([str(int(y)) for y in yrs])
                res.append({'Mecz': f"{h_t} vs {a_t}", 'Lata': lata_str, 'Ilość': len(yrs)})
            st.dataframe(pd.DataFrame(res).sort_values('Ilość', ascending=False), use_container_width=True)
        else: st.info("Brak.")

elif selected_page == "5. Gole (xG)":
    c1, c2 = st.columns(2); h5 = c1.text_input("H:", key="t5h"); a5 = c2.text_input("A:", key="t5a")
    if st.button("Oblicz Potencjał"):
        rh, ra = find_teams(df, h5, a5)
        if rh and ra:
            metrics = calculate_metrics(df, rh, ra)
            if metrics:
                xg_h, xg_a = metrics['xg_h'], metrics['xg_a']
                probs, _ = poisson_probability(xg_h, xg_a)
                st.markdown("### 📊 Analiza xG")
                col_xg1, col_xg2 = st.columns(2)
                col_xg1.metric(f"{rh}", f"{xg_h:.2f}")
                col_xg2.metric(f"{ra}", f"{xg_a:.2f}")
                st.write(f"**Over 1.5:** {probs['O1.5']*100:.1f}%")
                st.write(f"**Over 2.5:** {probs['O2.5']*100:.1f}%")
            else: st.error("Za mało danych.")

elif selected_page == "6. Remisy":
    c1, c2 = st.columns(2); h6=c1.text_input("H:", key="t6h"); a6=c2.text_input("A:", key="t6a")
    if st.button("Analiza Sił"):
        rh, ra = find_teams(df, h6, a6)
        if rh and ra:
            metrics = calculate_metrics(df, rh, ra)
            if metrics:
                xg_h, xg_a = metrics['xg_h'], metrics['xg_a']
                probs, _ = poisson_probability(xg_h, xg_a)
                draw_prob = probs['X'] * 100
                st.metric("Prawdopodobieństwo Remisu", f"{draw_prob:.1f}%")
                if abs(xg_h - xg_a) < 0.2: st.success("Siły bardzo wyrównane!")

elif selected_page == "7. Dokładny Wynik":
    c1, c2 = st.columns(2); h7=c1.text_input("H:", key="t7h"); a7=c2.text_input("A:", key="t7a")
    if st.button("Symulacja"):
        rh, ra = find_teams(df, h7, a7)
        if rh and ra:
            metrics = calculate_metrics(df, rh, ra)
            if metrics:
                xg_h, xg_a = metrics['xg_h'], metrics['xg_a']
                _, matrix = poisson_probability(xg_h, xg_a)
                st.markdown(f"**Przewidywane xG:** {xg_h:.2f} - {xg_a:.2f}")
                st.table(pd.DataFrame(matrix, columns=['Wynik', 'Szansa %']).head(5))

elif selected_page == "8. Rożne":
    c1, c2 = st.columns(2); h8=c1.text_input("H:", key="t8h"); a8=c2.text_input("A:", key="t8a")
    if st.button("Analiza Rożnych"):
        rh, ra = find_teams(df, h8, a8)
        if rh:
            dfc = df[df['HC']>0]
            mh = dfc[dfc['HomeTeam']==rh].tail(10); ma = dfc[dfc['AwayTeam']==ra].tail(10)
            if not mh.empty and not ma.empty:
                h_corners = (mh['HC'].mean() + ma['HC'].mean()) / 2
                a_corners = (ma['AC'].mean() + mh['AC'].mean()) / 2
                st.metric("Linia Rożnych", f"{(h_corners + a_corners):.1f}")
            else: st.warning("Brak danych.")

elif selected_page == "9. Kartki":
    c1, c2 = st.columns(2); h9=c1.text_input("H:", key="t9h"); a9=c2.text_input("A:", key="t9a")
    if st.button("Analiza Agresji"):
        rh, ra = find_teams(df, h9, a9)
        if rh:
            dfc = df[(df['HY']+df['AY'])>0]
            mh = dfc[dfc['HomeTeam']==rh].tail(15); ma = dfc[dfc['AwayTeam']==ra].tail(15)
            if not mh.empty and not ma.empty:
                h_pts = (mh['HY']*10 + mh['HR']*25).mean()
                a_pts = (ma['AY']*10 + ma['AR']*25).mean()
                h_prov = (mh['AY']*10 + mh['AR']*25).mean()
                a_prov = (ma['HY']*10 + ma['HR']*25).mean()
                exp_pts = ((h_pts + a_prov)/2) + ((a_pts + h_prov)/2)
                st.metric("Punkty Kartkowe", f"{exp_pts:.0f}")
            else: st.warning("Brak danych.")

elif selected_page == "10. BTTS":
    c1, c2 = st.columns(2); h10=c1.text_input("H:", key="t10h"); a10=c2.text_input("A:", key="t10a")
    if st.button("Sprawdź BTTS"):
        rh, ra = find_teams(df, h10, a10)
        if rh and ra:
            metrics = calculate_metrics(df, rh, ra)
            if metrics:
                xg_h, xg_a = metrics['xg_h'], metrics['xg_a']
                probs, _ = poisson_probability(xg_h, xg_a)
                btts_prob = probs['BTTS'] * 100
                st.metric("Szansa na BTTS", f"{btts_prob:.1f}%")

elif selected_page == "11. Perełki (Value)":
    thr = st.slider("Minimalna szansa (%)", 50, 90, 65)
    if st.button("Szukaj Okazji"):
        with st.spinner("Analizuję całą bazę..."):
            matches = []
            recent_games = df.tail(200)
            for index, row in recent_games.iterrows():
                h, a = row['HomeTeam'], row['AwayTeam']
                metrics = calculate_metrics(df, h, a)
                if metrics:
                    xg_h, xg_a = metrics['xg_h'], metrics['xg_a']
                    probs, _ = poisson_probability(xg_h, xg_a)
                    p_home = probs['1'] * 100
                    p_over = probs['O2.5'] * 100
                    if p_home >= thr:
                        matches.append({'Mecz': f"{h} vs {a}", 'Typ': '1 (Dom)', 'Szansa': f"{p_home:.1f}%"})
                    elif p_over >= thr:
                        matches.append({'Mecz': f"{h} vs {a}", 'Typ': 'Over 2.5', 'Szansa': f"{p_over:.1f}%"})
            if matches: st.dataframe(pd.DataFrame(matches), use_container_width=True)
            else: st.info("Brak wyraźnych okazji.")

elif selected_page == "12. Słownik":
    q = st.text_input("Wpisz nazwę drużyny:")
    if q:
        all_t = sorted(list(set(df['HomeTeam'].dropna()) | set(df['AwayTeam'].dropna())))
        m = [t for t in all_t if q.lower() in str(t).lower()]
        st.write(m)






