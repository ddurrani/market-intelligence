import streamlit as st
import requests
from newspaper import Article, Config
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Market Intelligence", layout="wide", initial_sidebar_state="collapsed")

# --- SESSION STATE ---
if 'all_articles' not in st.session_state:
    st.session_state.all_articles = []
if 'visible_count' not in st.session_state:
    st.session_state.visible_count = 20

# --- THE INTERCEPT STYLE CSS & GHOST MODE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Merriweather:wght@300;400;700&display=swap');

    /* --- GHOST MODE: SIDEBAR TOGGLE --- */
    [data-testid="stSidebarCollapsedControl"] {
        opacity: 0; 
        transition: opacity 0.3s ease;
    }
    [data-testid="stSidebarCollapsedControl"]:hover {
        opacity: 1 !important;
        background-color: #f0f0f0;
    }

    [data-testid="stDecoration"] { display: none; }

    /* --- TYPOGRAPHY --- */
    h1, h2, h3 {
        font-family: 'Oswald', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    h1 { font-size: 3.5rem !important; border-bottom: 4px solid black; padding-bottom: 10px; margin-bottom: 20px; }
    h3 { font-size: 1.5rem !important; margin-top: 0px; }

    p, div, li {
        font-family: 'Merriweather', serif !important;
        color: #1a1a1a;
        line-height: 1.6;
    }
    
    .stCaption {
        font-family: 'Oswald', sans-serif !important;
        color: #666666 !important;
        text-transform: uppercase;
        font-size: 0.9rem;
        border-top: 1px solid #000;
        padding-top: 5px;
        margin-top: 5px;
    }

    /* --- INPUT FIELDS --- */
    .stTextInput input {
        border: 2px solid black !important;
        border-radius: 0px !important;
        font-family: 'Oswald', sans-serif;
        padding: 10px;
        height: 45px;
        box-shadow: none !important;
        outline: none !important;
    }
    .stTextInput input:focus {
        border: 2px solid black !important;
        box-shadow: none !important;
    }
    
    /* --- RADIO BUTTONS --- */
    .stRadio label {
        font-family: 'Oswald', sans-serif !important;
        font-size: 1rem !important;
        color: black !important;
    }
    div[data-testid="stRadio"] {
        margin-top: -15px;
    }
    div[data-testid="stRadio"] > div {
        background-color: transparent;
    }
    
    /* --- BUTTONS --- */
    .stButton > button {
        border: 2px solid black !important;
        border-radius: 0px !important;
        background-color: #000000 !important;
        color: #ffffff !important;
        font-family: 'Oswald', sans-serif !important;
        text-transform: uppercase;
        font-weight: bold;
        height: 45px; 
        margin-top: 0px;
        width: 100%;
    }
    
    .stButton > button p { color: #ffffff !important; }

    .stButton > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    .stButton > button:hover p { color: #000000 !important; }

    /* --- EXPANDER --- */
    .streamlit-expanderHeader {
        font-family: 'Oswald', sans-serif;
        font-weight: bold;
        border: 1px solid black;
        border-radius: 0px;
        background-color: #f4f4f4;
    }
    
    /* --- WATERMARK --- */
    .watermark {
        position: fixed;
        bottom: 0px;
        right: 20px;
        padding: 8px 15px;
        background-color: #000000;
        color: white;
        font-family: 'Oswald', sans-serif;
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        z-index: 99999;
        pointer-events: none;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    section[data-testid="stSidebar"] {
        background-color: #f9f9f9;
        border-right: 1px solid #ddd;
    }
</style>

<div class="watermark">DEVELOPED BY DA DURRANI</div>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---

def fetch_news(api_key, topic, scope):
    """
    Fetches up to 100 articles in one go.
    We store these in session state and only display chunks of 20.
    """
    base_url = "https://newsapi.org/v2/everything"
    
    params = {
        "q": topic,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 100,  # Grab maximum allowed by free tier
        "apiKey": api_key
    }

    if scope == "Australian Sources":
        au_domains_list = [
            "abc.net.au", "skynews.com.au", "news.com.au", "9news.com.au",
            "dailytelegraph.com.au", "smh.com.au", "theage.com.au", "sbs.com.au",
            "heraldsun.com.au", "thegcminute.com.au", "cairnsnews.org",
            "canberratimes.com.au", "goldcoastbulletin.com.au", "businessnews.com.au",
            "tasmaniantimes.com", "alicespringsnews.com.au", "sydneysun.com",
            "perthnow.com.au", "brisbanetimes.com.au", "watoday.com.au", "afr.com",
            "theaustralian.com.au", "adelaidenow.com.au", "ntnews.com.au",
            "themercury.com.au", "examiner.com.au", "bordermail.com.au",
            "illawarramercury.com.au", "newcastleherald.com.au", "geelongadvertiser.com.au",
            "bendigoadvertiser.com.au", "thecourier.com.au", "standard.net.au",
            "theadvocate.com.au", "northerndailyleader.com.au", "dailyadvertiser.com.au",
            "couriermail.com.au", "morningbulletin.com.au", "gladstoneobserver.com.au",
            "frasercoastchronicle.com.au", "sunshinecoastdaily.com.au", "gympietimes.com.au",
            "tweeddailynews.com.au", "northernstar.com.au", "dailymercury.com.au",
            "theguardian.com"
        ]
        params["domains"] = ",".join(au_domains_list)

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json().get("articles", [])
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

def summarize_with_google_rest(text_content, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    prompt = f"You are a professional industry analyst. Read the following news article and provide a synopsis consisting of EXACTLY four bullet points. Format the output as a clean markdown list. Keep it professional, objective, and concise.\n\nArticle Text:\n{text_content}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200: return f"API Error {response.status_code}: {response.text}"
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e: return f"Connection Error: {e}"

def extract_and_summarize(article_url, google_api_key):
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    config = Config()
    config.browser_user_agent = user_agent
    config.request_timeout = 10 
    try:
        article = Article(article_url, config=config)
        article.download()
        article.parse()
        if len(article.text) < 200: return "⚠️ **Restricted Content:** This article appears to be behind a hard paywall or consists mainly of media. The AI cannot read the text."
        return summarize_with_google_rest(article.text, google_api_key)
    except Exception as e: return f"Error: Could not extract content ({str(e)}). The site may be blocking access."

def format_date(date_str):
    try: return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except: return date_str[:10]

# --- INTERFACE ---
with st.sidebar:
    st.markdown("### SYSTEM CONFIG")
    if "NEWS_API_KEY" in st.secrets: news_api_key = st.secrets["NEWS_API_KEY"]; st.success("✅ NEWS API KEY LOADED")
    else: news_api_key = st.text_input("NEWSAPI KEY", type="password")
    if "GOOGLE_API_KEY" in st.secrets: google_api_key = st.secrets["GOOGLE_API_KEY"]; st.success("✅ GOOGLE API KEY LOADED")
    else: google_api_key = st.text_input("GOOGLE API KEY", type="password")
    st.markdown("---"); st.caption("POWERED BY GEMINI 2.5 FLASH")

st.title("THE BRIEFING")
st.markdown("### LIVE NEWS INTELLIGENCE FEED")

col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
with col1: topic = st.text_input("SEARCH TOPIC OR INDUSTRY", placeholder="E.G. ARTIFICIAL INTELLIGENCE")
with col2: search_pressed = st.button("SEARCH", use_container_width=True)

opt1, opt2 = st.columns([4, 1])
with opt1: source_scope = st.radio("SELECT SOURCE REGION:", ["All Sources", "Australian Sources"], horizontal=True, label_visibility="collapsed")
with opt2: article_count_placeholder = st.empty()

st.markdown("---")

# --- MAIN LOGIC ---

# 1. NEW SEARCH: Fetch 100 articles, Reset visible count to 20
if search_pressed:
    if not news_api_key or not google_api_key:
        st.warning("⚠️ ACCESS DENIED: KEYS NOT FOUND.")
    elif not topic:
        st.warning("⚠️ INPUT ERROR: PLEASE ENTER A TOPIC.")
    else:
        st.session_state.visible_count = 20 # Reset visibility
        scope_text = "AUSTRALIAN WIRES" if source_scope == "Australian Sources" else "GLOBAL WIRES"
        
        with st.spinner(f"SCANNING {scope_text} FOR '{topic.upper()}'..."):
            # This grabs up to 100 items and stores them all
            fetched = fetch_news(news_api_key, topic, source_scope)
            st.session_state.all_articles = fetched

# 2. DISPLAY LOGIC (Slices the 'all_articles' list based on 'visible_count')
if st.session_state.all_articles:
    
    # We slice the master list: 0 to visible_count
    visible_articles = st.session_state.all_articles[:st.session_state.visible_count]
    
    # Display count
    article_count_placeholder.markdown(f"<h3 style='font-size: 1rem !important; text-align: center; margin-top: 0px;'>ARTICLES FOUND: {len(st.session_state.all_articles)}</h3>", unsafe_allow_html=True)
    
    # Loop through ONLY the visible subset
    for idx, art in enumerate(visible_articles):
        with st.container():
            st.markdown(f"### {idx+1}. {art['title']}")
            
            c1, c2 = st.columns([1, 5])
            with c1: st.caption(f"📅 {format_date(art['publishedAt'])}")
            with c2: st.caption(f"SOURCE: {art['source']['name'].upper()}")
            
            with st.expander("SHOW OVERVIEW"):
                with st.spinner("DECRYPTING & ANALYZING..."):
                    summary = extract_and_summarize(art['url'], google_api_key)
                    st.markdown(summary)
                    st.markdown(f"**[READ FULL SOURCE MATERIAL]({art['url']})**")
            
            st.markdown("<hr style='border-top: 2px solid black;'>", unsafe_allow_html=True)

    # 3. LOAD MORE BUTTON
    # If we have more articles in memory than we are currently showing
    if st.session_state.visible_count < len(st.session_state.all_articles):
        if st.button("LOAD NEXT 20 ARTICLES", use_container_width=True):
            st.session_state.visible_count += 20
            st.rerun() # Refresh page to show the larger slice

elif search_pressed:
    st.write("NO RECORDS FOUND.")
    article_count_placeholder.markdown("**ARTICLES FOUND: 0**")
