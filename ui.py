import streamlit as st

from sigcf_auth import BG_URL, link_instagram, logo_html

# Adicionamos a tag <style> no início e </style> no fim da variável de texto para o navegador entender o design
SIGCF_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
.stApp{
 background:linear-gradient(rgba(10,20,9,0.68),rgba(10,20,9,0.82)),
 url('__BG__') center center/cover no-repeat fixed!important;}
[data-testid="stAppViewContainer"]{background:transparent!important;}
[data-testid="stSidebar"]{
 background:rgba(10,20,9,0.96)!important;border-right:1px solid #1e2e1c!important;}
[data-testid="stSidebar"] *{color:#e8edd0!important;}
[data-testid="stHeader"]{background:rgba(10,20,9,0.45)!important;}
.block-container{background:transparent!important;max-width:1180px!important;}
h1,h2,h3,h4,p,span,label{color:#e8edd0;}
h1{font-family:'Barlow Condensed',sans-serif;letter-spacing:1px;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#9ab892!important;}
.sec{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
 letter-spacing:2px;text-transform:uppercase;color:#9ab892;
 border-left:4px solid #5a9452;padding-left:10px;margin:8px 0 12px;}
.ctx-box{background:rgba(13,24,12,0.88);border:1px solid #2a3d28;border-radius:12px;padding:14px 16px;margin-bottom:12px;}
.hub-card{background:rgba(17,28,16,0.86);border:1px solid #2a3d28;border-radius:14px;padding:18px 14px;
 text-align:center;min-height:118px;transition:border-color .2s;}
.hub-card.active{border-color:rgba(90,148,82,0.85);border-top:3px solid #5a9452;}
.hub-card.soon{opacity:.55;border-style:dashed;}
.hub-card .ico{font-size:28px;line-height:1;margin-bottom:8px;}
.hub-card .tit{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;
 color:#e8edd0;text-transform:uppercase;letter-spacing:.5px;line-height:1.25;}
.hub-card .tag{font-size:9px;font-weight:700;letter-spacing:1px;margin-top:8px;
 display:inline-block;padding:3px 10px;border-radius:10px;}
.hub-card.active .tag{background:rgba(26,58,24,0.9);color:#8ec486;border:1px solid #5a9452;}
.hub-card.soon .tag{background:#1a1a10;color:#8aab80;border:1px solid #3a4a38;}
.insta-link{display:inline-flex;align-items:center;gap:6px;color:#8ec486!important;
 text-decoration:none;font-weight:600;}
.insta-ico{width:17px;height:17px;flex-shrink:0;}
.stTextInput input,.stNumberInput input,.stTextArea textarea,
[data-testid="stDateInput"] input{
 background:#dce6d2!important;color:#1a2818!important;
 border:1px solid #4a6644!important;border-radius:8px!important;}
div[data-baseweb="select"] > div{
 background:#dce6d2!important;border:1px solid #4a6644!important;
 color:#1a2818!important;border-radius:8px!important;}
[data-testid="stForm"]{
 background:rgba(13,24,12,0.88)!important;border:1px solid #2a3d28!important;
 border-radius:12px;padding:12px 16px;}
div[data-testid="stMetric"]{background:rgba(13,24,12,0.88);border:1px solid #2a3d28;border-radius:10px;padding:10px 14px;}
div[data-testid="stMetric"] label{color:#9ab892!important;}
div[data-testid="stMetricValue"]{color:#8ec486!important;font-family:'Barlow Condensed',sans-serif;}
.stTabs [data-baseweb="tab-list"]{background:rgba(13,24,12,0.88);border-bottom:1px solid #2a3d28;gap:8px;}
.stTabs [data-baseweb="tab"]{
 color:#9ab892!important;font-family:'Barlow Condensed',sans-serif;font-weight:600;}
.stTabs [aria-selected="true"]{color:#e8edd0!important;border-bottom-color:#5a9452!important;}
.stButton button,[data-testid="stFormSubmitButton"] button{
 background:#4a9e3f!important;color:#ffffff!important;border:1px solid #6fa864!important;
 font-family:'Barlow Condensed',sans-serif;font-weight:700;letter-spacing:1.5px;
 text-transform:uppercase;border-radius:8px;min-height:44px;}
.stButton button:hover,[data-testid="stFormSubmitButton"] button:hover{background:#3d8534!important;}
</style>
"""


MODULOS_ORCAMENTO = [
    {"id": "lancamento", "nome": "Novo lancamento", "icone": "📝", "ativo": True},
    {"id": "consulta", "nome": "Consultar lancamentos", "icone": "🔍", "ativo": True},
    {"id": "tecnica", "nome": "Visao tecnica", "icone": "📊", "ativo": True},
    {"id": "planilha", "nome": "Painel planilha", "icone": "📁", "ativo": True},
    {"id": "orcamento", "nome": "Meta x realizado", "icone": "🎯", "ativo": False},
    {"id": "frota", "nome": "Cruzamento frota", "icone": "🚜", "ativo": False},
]


def aplicar_tema() -> None:
    st.markdown(SIGCF_CSS.replace("__BG__", BG_URL), unsafe_allow_html=True)


def render_header(titulo: str, subtitulo: str) -> None:
    col_logo, col_titulo, col_btn = st.columns([1.1, 4.5, 1.4])
    with col_logo:
        st.markdown(logo_html(118), unsafe_allow_html=True)
    with col_titulo:
        st.title(titulo)
        st.caption(subtitulo)
        st.markdown(f'<p style
