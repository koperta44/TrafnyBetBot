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
    page_title="TrafnyBetBot",
    page_icon=icon,
    layout="wide",
    initial_sidebar_state="collapsed" # Na start zwinięte
)

# --- 2. CSS (OSTATECZNA NAPRAWA STRZAŁKI DLA SAFARI) ---
st.markdown("""
    <style>
    /* 1. PRZYWRACAMY HEADER, ALE ROBIMY GO PRZEZROCZYSTYM */
    header {
        visibility: visible !important;
        background: transparent !important;
    }

    /* 2. UKRYWAMY DEKORACJĘ (KOLOROWY PASEK) */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* 3. UKRYWAMY MENU Z PRAWEJ (TRZY KROPKI, DEPLOY) */
    [data-testid="stToolbar"] {
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* 4. TO JEST KLUCZOWE: WYMUSZENIE WIDOCZNOŚCI STRZAŁKI (PRZYCISKU SIDEBARA) */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: block !important;
        color: #8742f5 !important; /* Twój fiolet */
        transform: scale(1.5); /* Powiększenie strzałki o 50% */
        top: 20px !important; /* Pozycja od góry */
        left: 20px !important; /* Pozycja od lewej */
        z-index: 1000001 !important; /* Musi być nad wszystkim innym */
    }
    
    /* 5. STOPKA */
    footer {visibility: hidden !important;}
    
    /* 6. CIEMNY MOTYW */
    .stApp {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    
    /* 7. PRZYCISKI */
    div.stButton > button {
        width: 100%;
        background-color: #8742f5;
        color: white;
        border: none;
        border-radius: 8px;
        height: 3.5em;
        font-weight: bold;
        font-size: 16px;
    }
    
    /* 8. INPUTY */
    [data-testid="stTextInput"] input, [data-testid="stSelectbox"] > div > div {
        background-color: #2d2d2d !important;
        color: white !important;
        border: 1px solid #444;
    }
    
    /* 9. MARGINESY DLA MOBILE - OBNIŻENIE TREŚCI */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 5rem !important; /* Dużo miejsca na górze dla strzałki */
            padding-left: 1rem !important;
            padding-right: 1rem !important;
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
    
    status = st.sidebar.empty()
    status.info("Łączenie...")
    
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
    
    status.empty()
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

# ==============================================================================
# PASEK BOCZNY (SIDEBAR) - TU JEST MENU
# ==============================================================================
with st.sidebar:
    try: st.image("icon.png", width=120)
    except: st.title("TrafnyBetBot")
    
    st.markdown("---")
    
    # 1. NAWIGACJA
    st.header("MENU GŁÓWNE")
    menu_options = [
        "1. Schematy", "2. Przeciwnik", "3. Łamak 1/2", "4. H2H Kalendarz", 
        "5. Gole", "6. Remisy", "7. Wynik", "8. Rożne", "9. Kartki", 
        "10. BTTS", "11. Perełki", "12. Słownik"
    ]
    # Przeniesienie wyboru do paska bocznego
    selected_page = st.selectbox("Wybierz narzędzie:", menu_options, label_visibility="collapsed")
    
    st.markdown("---")
    
    # 2. KONFIGURACJA
    st.markdown("### Baza Danych")
    opcje = {"1 rok (Szybko)":1, "5 lat":5, "10 lat":10, "15 lat":15}
    wybor = st.selectbox("Zakres historii:", list(opcje.keys()), index=0)
    
    if st.button("POBIERZ / ODŚWIEŻ"):
        with st.spinner("Pobieranie..."):
            st.session_state['df'] = pobierz_dane(opcje[wybor])
        st.success(f"Gotowe! Mecze: {len(st.session_state['df'])}")

# --- GŁÓWNY EKRAN ---

col_logo, col_title = st.columns([1, 5])
with col_logo:
    try: st.image("icon.png", width=50)
    except: st.write("⚽")
with col_title:
    st.title(selected_page)

if 'df' not in st.session_state or st.session_state['df'].empty:
    st.info("👈 Kliknij FIOLETOWĄ strzałkę '>' w lewym górnym rogu, aby otworzyć menu.")
    st.stop()

df = st.session_state['df']

# --- LOGIKA MODUŁÓW ---

if selected_page == "1. Schematy":
    if st.button("Skanuj Bazę"):
        teams = set(df['HomeTeam'])|set(df['AwayTeam']); res=[]
        for t in teams:
            d = df[(df['HomeTeam']==t)|(df['AwayTeam']==t)]
            if len(d)<5: continue
            hard = len(d[((d['HTR']=='H')&(d['FTR']=='A'))|((d['HTR']=='A')&(d['FTR']=='H'))])
            if hard>0: res.append({'Drużyna':t, 'Mecze':len(d), 'Łamaki':hard})
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("Top Drużyny")
            if res: st.dataframe(pd.DataFrame(res).sort_values('Łamaki', ascending=False).head(20), use_container_width=True)
        with c2:
            st.write("Top Pary")
            p = df[((df['HTR']=='H')&(df['FTR']=='A'))|((df['HTR']=='A')&(df['FTR']=='H'))]
            if not p.empty:
                cnt = p.groupby(['HomeTeam','AwayTeam']).size().reset_index(name='Ilość')
                st.dataframe(cnt[cnt['Ilość']>=2].sort_values('Ilość', ascending=False), use_container_width=True)
            else: st.info("Brak par.")

elif selected_page == "2. Przeciwnik":
    mt = st.text_input("Gospodarz (Ty):")
    if st.button("Szukaj") and mt:
        rh, _ = find_teams(df, mt, "x")
        if rh:
            cand=[]
            for op in (set(df['HomeTeam'])|set(df['AwayTeam'])):
                if op==rh: continue
                ma=df[df['AwayTeam']==op]
                choke=len(ma[(ma['HTR']=='A')&(ma['FTR']=='H')])
                if choke>0: cand.append({'Rywal':op, 'Wpadki':choke})
            if cand: st.dataframe(pd.DataFrame(cand).sort_values('Wpadki',ascending=False).head(20), use_container_width=True)
            else: st.info("Brak.")

elif selected_page == "3. Łamak 1/2":
    c1, c2 = st.columns(2)
    h = c1.text_input("Gosp:", key="t3h"); a = c2.text_input("Gość:", key="t3a")
    if st.button("Analizuj"):
        rh, ra = find_teams(df, h, a)
        if rh and ra:
            h_all = df[(df['HomeTeam']==rh)|(df['AwayTeam']==rh)]
            h_lam = len(h_all[((h_all['HTR']=='H')&(h_all['FTR']=='A'))|((h_all['HTR']=='A')&(h_all['FTR']=='H'))])
            a_all = df[(df['HomeTeam']==ra)|(df['AwayTeam']==ra)]
            a_lam = len(a_all[((a_all['HTR']=='H')&(a_all['FTR']=='A'))|((a_all['HTR']=='A')&(a_all['FTR']=='H'))])
            mh = df[df['HomeTeam']==rh]; ma = df[df['AwayTeam']==ra]
            h_lead = len(mh[mh['HTR']=='H']); h_choke = len(mh[(mh['HTR']=='H')&(mh['FTR']=='A')])
            hr = (h_choke/h_lead*100) if h_lead else 0
            a_trail = len(ma[ma['HTR']=='H']); a_come = len(ma[(ma['HTR']=='H')&(ma['FTR']=='A')])
            ac = (a_come/a_trail*100) if a_trail else 0
            st.metric("Szansa Matematyczna", f"{(hr+ac)/2:.1f}%")
            st.write(f"**{rh}:** {h_lam} łamaków ogółem.")
            st.write(f"**{ra}:** {a_lam} łamaków ogółem.")
            st.write(f"**Dom:** Oddał prowadzenie {h_choke} razy ({hr:.1f}%)")
            st.write(f"**Wyjazd:** Odrobił stratę {a_come} razy ({ac:.1f}%)")

elif selected_page == "4. H2H Kalendarz":
    m = st.slider("Miesiąc:", 1, 12, datetime.now().month)
    if st.button("Szukaj Serii"):
        lam = df[(((df['HTR']=='H')&(df['FTR']=='A'))|((df['HTR']=='A')&(df['FTR']=='H'))) & (df['Miesiac']==m)]
        if not lam.empty:
            pairs = lam.groupby(['HomeTeam','AwayTeam'])
            res = []
            for (h_t, a_t), g in pairs:
                yrs = sorted(g['Rok'].unique(), reverse=True)
                lata_str = " -> ".join([str(int(y)) for y in yrs])
                res.append({'Mecz': f"{h_t} vs {a_t}", 'Lata': lata_str})
            if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
            else: st.info("Brak par.")
        else: st.info("Brak.")

elif selected_page == "5. Gole":
    c1, c2 = st.columns(2); h5 = c1.text_input("H:", key="t5h"); a5 = c2.text_input("A:", key="t5a")
    if st.button("Oblicz"):
        rh, ra = find_teams(df, h5, a5)
        if rh and ra:
            mh = df[df['HomeTeam']==rh]; ma = df[df['AwayTeam']==ra]
            def gs(d, l, o): return len(d[(d['FTHG']+d['FTAG'])>l]) if o else len(d[(d['FTHG']+d['FTAG'])<l])
            data = {
                "Typ": ["Over 1.5", "Under 1.5", "Over 2.5", "Under 2.5"],
                "Szansa %": [
                    (gs(mh,1.5,1)/len(mh)+gs(ma,1.5,1)/len(ma))/2*100 if len(mh)*len(ma) else 0,
                    (gs(mh,1.5,0)/len(mh)+gs(ma,1.5,0)/len(ma))/2*100 if len(mh)*len(ma) else 0,
                    (gs(mh,2.5,1)/len(mh)+gs(ma,2.5,1)/len(ma))/2*100 if len(mh)*len(ma) else 0,
                    (gs(mh,2.5,0)/len(mh)+gs(ma,2.5,0)/len(ma))/2*100 if len(mh)*len(ma) else 0
                ]
            }
            st.table(pd.DataFrame(data).set_index("Typ").style.format("{:.1f}"))

elif selected_page == "6. Remisy":
    c1, c2 = st.columns(2); h6=c1.text_input("H:", key="t6h"); a6=c2.text_input("A:", key="t6a")
    if st.button("Sprawdź"):
        rh, ra = find_teams(df, h6, a6)
        if rh:
            p1=len(df[(df['HomeTeam']==rh)&(df['FTR']=='D')])/len(df[df['HomeTeam']==rh])*100 if len(df[df['HomeTeam']==rh]) else 0
            p2=len(df[(df['AwayTeam']==ra)&(df['FTR']=='D')])/len(df[df['AwayTeam']==ra])*100 if len(df[df['AwayTeam']==ra]) else 0
            st.metric("Szansa", f"{(p1+p2)/2:.1f}%")

elif selected_page == "7. Wynik":
    c1, c2 = st.columns(2); h7=c1.text_input("H:", key="t7h"); a7=c2.text_input("A:", key="t7a")
    if st.button("SYMULUJ"):
        rh, ra = find_teams(df, h7, a7)
        if rh and ra:
            try:
                mr = df[df['HomeTeam'] == rh].iloc[-1] if not df[df['HomeTeam'] == rh].empty else None
                if mr is not None:
                    liga = mr['Liga']; dfl = df[df['Liga']==liga].tail(500)
                    avg_hg = dfl['FTHG'].mean() if not dfl.empty else 1.3
                    avg_ag = dfl['FTAG'].mean() if not dfl.empty else 1.1
                else: avg_hg = 1.3; avg_ag = 1.1
                if avg_hg==0: avg_hg=1.0
                if avg_ag==0: avg_ag=1.0
                mh = df[df['HomeTeam']==rh].tail(20); ma = df[df['AwayTeam']==ra].tail(20)
                if not mh.empty and not ma.empty:
                    ha = mh['FTHG'].mean()/avg_hg; hd = mh['FTAG'].mean()/avg_ag
                    aa = ma['FTAG'].mean()/avg_ag; ad = ma['FTHG'].mean()/avg_hg
                    xg_h = ha * ad * avg_hg; xg_a = aa * hd * avg_ag
                    st.write(f"**xG:** {rh} {xg_h:.2f} - {xg_a:.2f} {ra}")
                    def poisson(k, lam): return (math.exp(-lam)*(lam**k))/math.factorial(k)
                    res=[]
                    for i in range(5):
                        for j in range(5):
                            p = poisson(i, xg_h) * poisson(j, xg_a) * 100
                            if p > 5: res.append((f"{i}:{j}", p))
                    res.sort(key=lambda x:x[1], reverse=True)
                    for r in res: st.write(f"{r[0]} ({r[1]:.1f}%)")
                else: st.warning("Za mało meczów.")
            except: st.error("Błąd obliczeń.")

elif selected_page == "8. Rożne":
    c1, c2 = st.columns(2); h8=c1.text_input("H:", key="t8h"); a8=c2.text_input("A:", key="t8a")
    if st.button("Analiza"):
        rh, ra = find_teams(df, h8, a8)
        if rh:
            dfc = df[df['HC']>0]
            mh=dfc[dfc['HomeTeam']==rh]; ma=dfc[dfc['AwayTeam']==ra]
            if not mh.empty and not ma.empty:
                h_avg = mh['HC'].mean()+mh['AC'].mean(); a_avg = ma['HC'].mean()+ma['AC'].mean()
                st.metric("Średnia suma", f"{(h_avg+a_avg)/2:.1f}")
            else: st.warning("Brak danych.")

elif selected_page == "9. Kartki":
    c1, c2 = st.columns(2); h9=c1.text_input("H:", key="t9h"); a9=c2.text_input("A:", key="t9a")
    if st.button("Analiza"):
        rh, ra = find_teams(df, h9, a9)
        if rh:
            dfc = df[(df['HY']+df['AY'])>0]
            mh=dfc[dfc['HomeTeam']==rh]; ma=dfc[dfc['AwayTeam']==ra]
            if not mh.empty and not ma.empty:
                hp=(mh['HY']+2*mh['HR']).mean(); ap=(ma['AY']+2*ma['AR']).mean()
                st.metric("Punkty", f"{hp+ap:.1f}")
            else: st.warning("Brak danych.")

elif selected_page == "10. BTTS":
    c1, c2 = st.columns(2); h10=c1.text_input("H:", key="t10h"); a10=c2.text_input("A:", key="t10a")
    if st.button("Sprawdź"):
        rh, ra = find_teams(df, h10, a10)
        if rh:
            mh=df[df['HomeTeam']==rh]; hp=len(mh[(mh['FTHG']>0)&(mh['FTAG']>0)])/len(mh)*100 if len(mh) else 0
            ma=df[df['AwayTeam']==ra]; ap=len(ma[(ma['FTHG']>0)&(ma['FTAG']>0)])/len(ma)*100 if len(ma) else 0
            st.metric("Szansa", f"{(hp+ap)/2:.1f}%")

elif selected_page == "11. Perełki":
    thr = st.slider("Próg szansy (%)", 10, 100, 30)
    if st.button("Generuj Listy"):
        with st.spinner("Przetwarzanie..."):
            teams_stats = {} 
            all_teams = set(df['HomeTeam']) | set(df['AwayTeam'])
            for t in all_teams:
                mh = df[df['HomeTeam'] == t]; ma = df[df['AwayTeam'] == t]
                if len(mh) < 5 or len(ma) < 5: continue
                h_leads = len(mh[mh['HTR']=='H']); h_chokes = len(mh[(mh['HTR']=='H')&(mh['FTR']=='A')])
                h_risk = (h_chokes / h_leads * 100) if h_leads > 0 else 0
                a_trails = len(ma[ma['HTR']=='H']); a_come = len(ma[(ma['HTR']=='H')&(ma['FTR']=='A')])
                a_chance = (a_come / a_trails * 100) if a_trails > 0 else 0
                if h_risk > 0 or a_chance > 0:
                    l = mh.iloc[-1]['Liga'] if not mh.empty else ma.iloc[-1]['Liga']
                    teams_stats[t] = {'L': l, 'HR': h_risk, 'AC': a_chance}
            real = []; glo = []
            for h, d1 in teams_stats.items():
                for a, d2 in teams_stats.items():
                    if h == a: continue
                    prob = (d1['HR'] + d2['AC']) / 2
                    if prob >= thr:
                        desc = {'Mecz': f"{h} vs {a}", 'Liga': d1['L'], 'Szansa': f"{prob:.1f}%", 'prob_num': prob}
                        glo.append(desc)
                        if d1['L'] == d2['L']: real.append(desc)
        st.write("Ta sama liga")
        if real: st.dataframe(pd.DataFrame(real).sort_values('prob_num', ascending=False).drop(columns=['prob_num']), use_container_width=True)
        else: st.info("Brak.")
        st.write("Cały świat")
        if glo: st.dataframe(pd.DataFrame(glo).sort_values('prob_num', ascending=False).head(200).drop(columns=['prob_num']), use_container_width=True)
        else: st.info("Brak.")

elif selected_page == "12. Słownik":
    q = st.text_input("Szukaj:")
    if q:
        all_t = sorted(list(set(df['HomeTeam'].dropna()) | set(df['AwayTeam'].dropna())))
        m = [t for t in all_t if q.lower() in str(t).lower()]
        st.write(m)





