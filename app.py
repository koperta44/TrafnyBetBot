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
    layout="wide", # Ważne dla mobile - wykorzystuje całą szerokość
    initial_sidebar_state="auto"
)

# --- 2. CSS: MOBILE OPTIMIZATION & DARK MODE ---
st.markdown("""
    <style>
    /* 1. Ukrycie zbędnych elementów Streamlit */
    [data-testid="stToolbar"] {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* 2. Ciemny motyw wymuszony */
    .stApp {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    
    /* 3. MOBILE TWEAKS (Kluczowe dla responsywności) */
    @media (max-width: 768px) {
        /* Zmniejszenie marginesów na telefonie - więcej miejsca na treść */
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        /* Powiększenie czcionki w tabelach, żeby dało się czytać palcem */
        [data-testid="stDataFrame"] {
            font-size: 14px !important;
        }
        /* Przyciski większe na dotyk */
        div.stButton > button {
            height: 3.5em !important;
        }
    }
    
    /* 4. Stylizacja Przycisków - Twój Fiolet */
    div.stButton > button {
        width: 100%;
        background-color: #8742f5;
        color: white;
        border: none;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
        font-size: 16px;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #6a25c9;
        border: 1px solid white;
    }
    
    /* 5. Inputy na ciemno */
    [data-testid="stTextInput"] input {
        background-color: #2d2d2d;
        color: white;
        border: 1px solid #444;
    }
    
    /* Wyśrodkowanie logo */
    [data-testid="stSidebar"] img {
        display: block;
        margin-left: auto;
        margin-right: auto;
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

# --- FUNKCJE ---
@st.cache_data(ttl=3600)
def pobierz_dane(ile_lat):
    curr_y = 25; start_y = curr_y - ile_lat
    sezony = [f"{i:02d}{i+1:02d}" for i in range(start_y, curr_y+1)]; sezony.reverse()
    wszystkie = []
    
    status = st.empty()
    status.info("Inicjowanie połączenia...")
    
    total = len(sezony) * len(LIGI_KODY)
    done = 0
    
    for s in sezony:
        for n, k in LIGI_KODY.items():
            try:
                r = requests.get(f"https://www.football-data.co.uk/mmz4281/{s}/{k}.csv", timeout=1)
                if r.status_code==200:
                    df = pd.read_csv(io.StringIO(r.text))
                    df = clean_df(df, n, s)
                    wszystkie.append(df)
            except: pass
            done += 1
            if done % 50 == 0: status.text(f"Pobieranie danych... {int(done/total*100)}%")
            
    for n, k in LIGI_KODY.items():
        try:
            r = requests.get(f"https://www.football-data.co.uk/new/{k}.csv", timeout=1)
            if r.status_code==200:
                df = pd.read_csv(io.StringIO(r.text)); df = clean_df(df, n, "Current")
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

def clean_df(df, n, s):
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={'Home':'HomeTeam','Away':'AwayTeam','Res':'FTR','Result':'FTR'})
    req=['Date','HomeTeam','AwayTeam','HTR','FTR','FTHG','FTAG']
    opt=['HC','AC','HY','AY','HR','AR']
    for c in opt: 
        if c not in df.columns: df[c]=0
        else: df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0).astype(int)
    if 'FTR' not in df.columns: df['FTR']='D'
    if set(['HomeTeam','AwayTeam']).issubset(df.columns):
        df['Liga']=n
        if 'Date' in df.columns:
            df['Date']=pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df['Rok']=df['Date'].dt.year; df['Miesiac']=df['Date'].dt.month
        return df[list(set(req+opt+['Liga','Rok','Miesiac'])&set(df.columns))]
    return pd.DataFrame()

def find_teams(df, h, a):
    all_t = set(df['HomeTeam'])|set(df['AwayTeam'])
    rh = next((t for t in all_t if h.lower() in str(t).lower()), None)
    ra = next((t for t in all_t if a.lower() in str(t).lower()), None)
    return rh, ra

# --- SIDEBAR ---
with st.sidebar:
    try: st.image("icon.png", width=140)
    except: st.title("TrafnyBetBot")
    
    st.markdown("---")
    opcje = {"1 rok":1, "5 lat":5, "10 lat":10, "15 lat":15}
    wybor = st.selectbox("Zakres:", list(opcje.keys()), index=1)
    
    if st.button("POBIERZ BAZĘ DANYCH"):
        with st.spinner("Pobieranie..."):
            st.session_state['df'] = pobierz_dane(opcje[wybor])
        st.success(f"Gotowe! Mecze: {len(st.session_state['df'])}")
    
    st.markdown("---")
    st.caption("Wersja WEB 2.1 (Mobile)")

# --- APP ---
if 'df' not in st.session_state:
    st.info("👈 Rozpocznij od pobrania bazy w menu bocznym.")
    st.stop()

df = st.session_state['df']

tabs = st.tabs([
    "Schematy", "Przeciwnik", "Łamak", "Serie", "Gole", "Remisy",
    "Wynik", "Rożne", "Kartki", "BTTS", "Perełki", "Słownik"
])

# 1. SCHEMATY
with tabs[0]:
    if st.button("Skanuj Bazę"):
        teams = set(df['HomeTeam'])|set(df['AwayTeam']); res=[]
        for t in teams:
            d = df[(df['HomeTeam']==t)|(df['AwayTeam']==t)]
            if len(d)<10: continue
            hard = len(d[((d['HTR']=='H')&(d['FTR']=='A'))|((d['HTR']=='A')&(d['FTR']=='H'))])
            if hard>0: res.append({'Drużyna':t, 'Mecze':len(d), 'Łamaki':hard})
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("Top Drużyny")
            if res: st.dataframe(pd.DataFrame(res).sort_values('Łamaki', ascending=False).head(20), use_container_width=True)
        with c2:
            st.write("Top Pary H2H")
            p = df[((df['HTR']=='H')&(df['FTR']=='A'))|((df['HTR']=='A')&(df['FTR']=='H'))]
            if not p.empty:
                cnt = p.groupby(['HomeTeam','AwayTeam']).size().reset_index(name='Ilość')
                st.dataframe(cnt[cnt['Ilość']>=2].sort_values('Ilość', ascending=False), use_container_width=True)
            else: st.info("Brak par.")

# 2. PRZECIWNIK
with tabs[1]:
    st.write("Szukaj Ofiary")
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

# 3. ŁAMAK (Fixed Logic)
with tabs[2]:
    st.write("Analiza 1/2")
    c1, c2 = st.columns(2)
    h = c1.text_input("Gosp:", key="t3h"); a = c2.text_input("Gość:", key="t3a")
    if st.button("Analizuj"):
        rh, ra = find_teams(df, h, a)
        if rh and ra:
            # A. HISTORIA
            h_all = df[(df['HomeTeam']==rh)|(df['AwayTeam']==rh)]
            h_lam = len(h_all[((h_all['HTR']=='H')&(h_all['FTR']=='A'))|((h_all['HTR']=='A')&(h_all['FTR']=='H'))])
            a_all = df[(df['HomeTeam']==ra)|(df['AwayTeam']==ra)]
            a_lam = len(a_all[((a_all['HTR']=='H')&(a_all['FTR']=='A'))|((a_all['HTR']=='A')&(a_all['FTR']=='H'))])
            
            # B. SCENARIUSZ
            mh = df[df['HomeTeam']==rh]; ma = df[df['AwayTeam']==ra]
            h_lead = len(mh[mh['HTR']=='H']); h_choke = len(mh[(mh['HTR']=='H')&(mh['FTR']=='A')])
            hr = (h_choke/h_lead*100) if h_lead else 0
            a_trail = len(ma[ma['HTR']=='H']); a_come = len(ma[(ma['HTR']=='H')&(ma['FTR']=='A')])
            ac = (a_come/a_trail*100) if a_trail else 0
            
            st.metric("Szansa Matematyczna", f"{(hr+ac)/2:.1f}%")
            st.write(f"**{rh}:** {h_lam} łamaków w historii.")
            st.write(f"**{ra}:** {a_lam} łamaków w historii.")
            st.write(f"**{rh} (Dom):** Oddał prowadzenie {h_choke} razy ({hr:.1f}%)")
            st.write(f"**{ra} (Wyjazd):** Odrobił stratę {a_come} razy ({ac:.1f}%)")

# 4. H2H KALENDARZ (Fixed Logic)
with tabs[3]:
    st.write("Serie H2H w miesiącu")
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
            else: st.info("Brak.")
        else: st.info("Brak łamaków w tym miesiącu.")

# 5. GOLE
with tabs[4]:
    st.write("Gole Over/Under")
    c1, c2 = st.columns(2)
    h5 = c1.text_input("H:", key="t5h"); a5 = c2.text_input("A:", key="t5a")
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

# 6. REMISY
with tabs[5]:
    st.write("Remis")
    c1, c2 = st.columns(2); h6=c1.text_input("H:", key="t6h"); a6=c2.text_input("A:", key="t6a")
    if st.button("Sprawdź"):
        rh, ra = find_teams(df, h6, a6)
        if rh:
            p1=len(df[(df['HomeTeam']==rh)&(df['FTR']=='D')])/len(df[df['HomeTeam']==rh])*100 if len(df[df['HomeTeam']==rh]) else 0
            p2=len(df[(df['AwayTeam']==ra)&(df['FTR']=='D')])/len(df[df['AwayTeam']==ra])*100 if len(df[df['AwayTeam']==ra]) else 0
            st.metric("Szansa", f"{(p1+p2)/2:.1f}%")

# 7. DOKŁADNY WYNIK
with tabs[6]:
    st.write("Symulacja Wyniku")
    c1, c2 = st.columns(2); h7=c1.text_input("H:", key="t7h"); a7=c2.text_input("A:", key="t7a")
    if st.button("SYMULUJ"):
        rh, ra = find_teams(df, h7, a7)
        if rh:
            try:
                l=df[df['HomeTeam']==rh]['Liga'].iloc[0]; dfl=df[df['Liga']==l].tail(500)
                avg_hg=dfl['FTHG'].mean(); avg_ag=dfl['FTAG'].mean()
                mh=df[df['HomeTeam']==rh].tail(20); ma=df[df['AwayTeam']==ra].tail(20)
                ha=mh['FTHG'].mean()/avg_hg; hd=mh['FTAG'].mean()/avg_ag
                aa=ma['FTAG'].mean()/avg_ag; ad=ma['FTHG'].mean()/avg_hg
                xg_h=ha*ad*avg_hg; xg_a=aa*hd*avg_ag
                st.write(f"xG: {xg_h:.2f} - {xg_a:.2f}")
                res=[]
                for i in range(5):
                    for j in range(5):
                        p=(math.exp(-xg_h)*(xg_h**i)/math.factorial(i)) * (math.exp(-xg_a)*(xg_a**j)/math.factorial(j))*100
                        if p>5: res.append((f"{i}:{j}", p))
                res.sort(key=lambda x:x[1], reverse=True)
                for r in res: st.write(f"{r[0]} ({r[1]:.1f}%)")
            except: st.error("Błąd.")

# 8. ROŻNE
with tabs[7]:
    st.write("Rożne")
    c1, c2 = st.columns(2); h8=c1.text_input("H:", key="t8h"); a8=c2.text_input("A:", key="t8a")
    if st.button("Analiza Rożnych"):
        rh, ra = find_teams(df, h8, a8)
        if rh:
            dfc = df[df['HC']>0]
            mh=dfc[dfc['HomeTeam']==rh]; ma=dfc[dfc['AwayTeam']==ra]
            if not mh.empty and not ma.empty:
                havg = mh['HC'].mean()+mh['AC'].mean(); aavg = ma['HC'].mean()+ma['AC'].mean()
                st.metric("Średnia suma", f"{(havg+aavg)/2:.1f}")
            else: st.warning("Brak danych.")

# 9. KARTKI
with tabs[8]:
    st.write("Kartki")
    c1, c2 = st.columns(2); h9=c1.text_input("H:", key="t9h"); a9=c2.text_input("A:", key="t9a")
    if st.button("Analiza Kartek"):
        rh, ra = find_teams(df, h9, a9)
        if rh:
            dfc = df[(df['HY']+df['AY'])>0]
            mh=dfc[dfc['HomeTeam']==rh]; ma=dfc[dfc['AwayTeam']==ra]
            if not mh.empty and not ma.empty:
                hpts=(mh['HY']+2*mh['HR']).mean(); apts=(ma['AY']+2*ma['AR']).mean()
                st.metric("Punkty (Y=1, R=2)", f"{hpts+apts:.1f}")
            else: st.warning("Brak danych.")

# 10. BTTS
with tabs[9]:
    st.write("BTTS")
    c1, c2 = st.columns(2); h10=c1.text_input("H:", key="t10h"); a10=c2.text_input("A:", key="t10a")
    if st.button("Sprawdź BTTS"):
        rh, ra = find_teams(df, h10, a10)
        if rh:
            mh=df[df['HomeTeam']==rh]; hp=len(mh[(mh['FTHG']>0)&(mh['FTAG']>0)])/len(mh)*100 if len(mh) else 0
            ma=df[df['AwayTeam']==ra]; ap=len(ma[(ma['FTHG']>0)&(ma['FTAG']>0)])/len(ma)*100 if len(ma) else 0
            st.metric("Szansa", f"{(hp+ap)/2:.1f}%")

# 11. PEREŁKI (Bez koszyków)
with tabs[10]:
    st.write("Generator Perełek")
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
                        
        c1, c2 = st.columns(2)
        with c1:
            st.write("Ta sama liga (Realne)")
            if real: st.dataframe(pd.DataFrame(real).sort_values('prob_num', ascending=False).drop(columns=['prob_num']), use_container_width=True)
            else: st.info("Brak.")
        with c2:
            st.write("Cały świat (Teoretyczne - Top 200)")
            if glo: st.dataframe(pd.DataFrame(glo).sort_values('prob_num', ascending=False).head(200).drop(columns=['prob_num']), use_container_width=True)
            else: st.info("Brak.")

# 12. SŁOWNIK
with tabs[11]:
    st.write("Słownik Drużyn")
    q = st.text_input("Szukaj:")
    if q:
        all_t = sorted(list(set(df['HomeTeam'].dropna()) | set(df['AwayTeam'].dropna())))
        m = [t for t in all_t if q.lower() in str(t).lower()]
        st.write(m)
