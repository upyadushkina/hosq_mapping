import streamlit as st
import pandas as pd
from pyvis.network import Network
import tempfile
import base64
import os
import json

# === Цветовая схема и параметры ===
PAGE_BG_COLOR = "#262123"              # фон всей страницы
PAGE_TEXT_COLOR = "#E8DED3"            # основной цвет текста
SIDEBAR_BG_COLOR = "#262123"           # фон боковой панели
SIDEBAR_LABEL_COLOR = "#E8DED3"        # подписи к фильтрам
SIDEBAR_TAG_TEXT_COLOR = "#E8DED3"     # текст в тегах
SIDEBAR_TAG_BG_COLOR = "#6A50FF"       # фон выбранного тега
BUTTON_BG_COLOR = "#262123"            # фон кнопки
BUTTON_TEXT_COLOR = "#4C4646"          # цвет текста на кнопке
HEADER_MENU_COLOR = "#262123"          # цвет верхнего меню Streamlit

# === Настройки страницы ===
st.set_page_config(page_title="Artists Graph", layout="wide")

# === CSS стилизация ===
st.markdown(f"""
    <style>
    body, .stApp {{
        background-color: {PAGE_BG_COLOR};
        color: {PAGE_TEXT_COLOR};
    }}
    .stSidebar {{
        background-color: {SIDEBAR_BG_COLOR} !important;
    }}
    .stSidebar label, .stSidebar .css-1n76uvr {{
        color: {SIDEBAR_LABEL_COLOR} !important;
    }}
    .stMultiSelect>div>div {{
        background-color: {PAGE_BG_COLOR} !important;
        color: {PAGE_TEXT_COLOR} !important;
    }}
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: {SIDEBAR_TAG_BG_COLOR} !important;
        color: {SIDEBAR_TAG_TEXT_COLOR} !important;
    }}
    .stButton > button {{
        background-color: {BUTTON_BG_COLOR} !important;
        color: {BUTTON_TEXT_COLOR} !important;
        border: none;
    }}
    header {{
        background-color: {HEADER_MENU_COLOR} !important;
    }}
    iframe {{
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        margin-top: 60px;
    }}
    </style>
""", unsafe_allow_html=True)

# === Загрузка данных ===
df = pd.read_csv("Etudes Lab 1 artistis.csv").fillna("")
df["professional field"] = df["professional field"].astype(str)

# Распарсим страну и город из 'country and city'
df["country"] = df["country and city"].apply(lambda x: x.split(",")[0].strip() if "," in x else x.strip())
df["city"] = df["country and city"].apply(lambda x: x.split(",")[1].strip() if "," in x else "")

# === Фильтры ===
st.sidebar.header("Filters")
all_countries = sorted(df["country"].unique().tolist())
all_cities = sorted(set(df["city"].dropna().tolist()) - {""})
all_fields = sorted(set(
    field.strip()
    for sublist in df["professional field"].dropna().str.split(",")
    for field in sublist if field.strip()
))

selected_countries = st.sidebar.multiselect("Filter by Country", all_countries)
selected_cities = st.sidebar.multiselect("Filter by City", all_cities)
selected_fields = st.sidebar.multiselect("Filter by Field", all_fields)

if st.sidebar.button("Clear filters"):
    selected_countries = []
    selected_cities = []
    selected_fields = []

# === Фильтрация данных ===
filtered_df = df.copy()
if selected_countries:
    filtered_df = filtered_df[filtered_df["country"].isin(selected_countries)]
if selected_cities:
    filtered_df = filtered_df[filtered_df["city"].isin(selected_cities)]
if selected_fields:
    filtered_df = filtered_df[filtered_df["professional field"].apply(lambda x: any(f.strip() in x for f in selected_fields))]

# === Подготовка графа ===
net = Network(height="700px", width="100%", bgcolor=PAGE_BG_COLOR, font_color=PAGE_TEXT_COLOR)

NODE_NAME_COLOR = "#4C4646"
NODE_CITY_COLOR = "#6A50FF"
NODE_FIELD_COLOR = "#B1D3AA"

for _, row in filtered_df.iterrows():
    name = row["name"].strip()
    city = row["city"].strip()
    country = row["country"].strip()
    location = f"{country}, {city}" if city else country
    fields = [f.strip() for f in row["professional field"].split(",") if f.strip()]
    photo = row["photo"].strip()
    telegram = row["telegram nickname"].strip()
    email = row["email"].strip()

    popup = f"""
    <div style='text-align:center; padding: 10px;'>
        <div style='font-weight:bold; font-size: 14px; margin-bottom: 5px;'>{name}</div>
        {f"<img src='{photo}' width='100' style='border-radius: 6px;'><br>" if photo else ""}
        {f"<b>Telegram:</b> {telegram}<br>" if telegram else ""}
        {f"<b>Email:</b> {email}<br>" if email else ""}
    </div>
    """

    net.add_node(name, label=name, title=popup, color=NODE_NAME_COLOR, shape="dot", size=20)
    if location:
        net.add_node(location, label=location, title=location, color=NODE_CITY_COLOR, shape="dot", size=10)
        net.add_edge(name, location)
    for field in fields:
        net.add_node(field, label=field, title=field, color=NODE_FIELD_COLOR, shape="dot", size=10)
        net.add_edge(name, field)

net.set_options(json.dumps({
  "interaction": {
    "hover": True,
    "tooltipDelay": 100,
    "navigationButtons": True,
    "selectConnectedEdges": True
  },
  "nodes": {
    "font": {"size": 0},
    "opacity": 1.0
  },
  "edges": {
    "color": {"color": "#4C4646", "highlight": "#6A50FF", "opacity": 0.8},
    "width": 1
  },
  "physics": {
    "enabled": True,
    "barnesHut": {
      "gravitationalConstant": -30000,
      "centralGravity": 0.2,
      "springLength": 300,
      "springConstant": 0.01,
      "damping": 0.1,
      "avoidOverlap": 1
    }
  }
}))

# === Генерация HTML и отображение ===
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
net.save_graph(temp_file.name)

if os.path.exists(temp_file.name):
    with open(temp_file.name, "r", encoding="utf-8") as f:
        html_code = f.read()
    st.components.v1.html(html_code, height=700)
else:
    st.error("Graph file was not created.")
