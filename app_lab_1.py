import streamlit as st
import pandas as pd
from pyvis.network import Network
import tempfile
import base64
import os
import json

# === Цветовая схема и параметры ===
PAGE_BG_COLOR = "#262123"
PAGE_TEXT_COLOR = "#E8DED3"
SIDEBAR_BG_COLOR = "#262123"
SIDEBAR_LABEL_COLOR = "#E8DED3"
SIDEBAR_TAG_TEXT_COLOR = "#E8DED3"
SIDEBAR_TAG_BG_COLOR = "#6A50FF"
BUTTON_BG_COLOR = "#262123"
BUTTON_TEXT_COLOR = "#4C4646"
BUTTON_CLEAN_TEXT_COLOR = "#E8DED3"
SIDEBAR_HEADER_COLOR = "#E8DED3"  # цвет заголовка Filters
SIDEBAR_TOGGLE_ARROW_COLOR = "#E8DED3"  # цвет стрелки бокового меню
HEADER_MENU_COLOR = "#262123"
GRAPH_LABEL_COLOR = "#E8DED3"

# === Настройки страницы ===
st.set_page_config(page_title="HOSQ Artists Mapping", layout="wide")

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
    .stSidebar h1, .stSidebar h2, .stSidebar h3 {{
        color: {SIDEBAR_HEADER_COLOR} !important;
    }}
    .stSidebar .css-ewr7em svg {{
        stroke: {SIDEBAR_TOGGLE_ARROW_COLOR} !important;
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
        color: {BUTTON_CLEAN_TEXT_COLOR} !important;
        border: none;
    }}
    .artist-card * {{
        color: {PAGE_TEXT_COLOR} !important;
    }}
    header {{
        background-color: {HEADER_MENU_COLOR} !important;
    }}
    iframe {{
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        margin-top: 0px;
    }}
    </style>
""", unsafe_allow_html=True)

# === Загрузка данных ===
df = pd.read_csv("Etudes Lab 1 artistis.csv").fillna("")
df["professional field"] = df["professional field"].astype(str)
df["role"] = df["role"].astype(str)

# Распарсим страну и город из 'country and city'
df["country"] = df["country and city"].apply(lambda x: x.split(",")[0].strip() if "," in x else x.strip())
df["city"] = df["country and city"].apply(lambda x: x.split(",")[1].strip() if "," in x else "")

# === Фильтры ===
st.sidebar.header("Filters")
all_fields = sorted(set(
    field.strip()
    for sublist in df["professional field"].dropna().str.split(",")
    for field in sublist if field.strip()
))
all_roles = sorted(set(
    role.strip()
    for sublist in df["role"].dropna().str.split(",")
    for role in sublist if role.strip()
))
all_countries = sorted(df["country"].unique().tolist())
all_cities = sorted(set(df["city"].dropna().tolist()) - {""})

selected_fields = st.sidebar.multiselect("Filter by Field", all_fields)
selected_roles = st.sidebar.multiselect("Filter by Role", all_roles)
selected_countries = st.sidebar.multiselect("Filter by Country", all_countries)
selected_cities = st.sidebar.multiselect("Filter by City", all_cities)

# === Выбор художника ===
artist_names = df["name"].dropna().unique().tolist()
selected_artist = st.sidebar.selectbox("🎨 Choose artist", [""] + artist_names)

# === Отображение карточки выбранного художника в боковой панели ===
if selected_artist and selected_artist in df["name"].values:
    artist = df[df["name"] == selected_artist].iloc[0]
    st.sidebar.markdown("---")
    with st.sidebar.container():
        st.markdown(f"<div class='artist-card'><h4>🎨 {artist['name']}</h4>", unsafe_allow_html=True)
        if artist['photo url']:
            st.image(artist['photo url'], width=200)
        else:
            st.image("https://static.tildacdn.com/tild3532-6664-4163-b538-663866613835/hosq-design-NEW.png", width=200)
        if artist['telegram nickname']:
            st.markdown(f"**Telegram:** {artist['telegram nickname']}")
        if artist['email']:
            st.markdown(f"**Email:** {artist['email']}")
        st.markdown("</div>", unsafe_allow_html=True)

# === Фильтрация данных ===
filtered_df = df.copy()
if selected_fields:
    filtered_df = filtered_df[filtered_df["professional field"].apply(lambda x: any(f.strip() in x for f in selected_fields))]
if selected_roles:
    filtered_df = filtered_df[filtered_df["role"].apply(lambda x: any(r.strip() in x for r in selected_roles))]
if selected_countries:
    filtered_df = filtered_df[filtered_df["country"].isin(selected_countries)]
if selected_cities:
    filtered_df = filtered_df[filtered_df["city"].isin(selected_cities)]

# === Подготовка графа ===
net = Network(height="100vh", width="100%", bgcolor=PAGE_BG_COLOR, font_color=PAGE_TEXT_COLOR)

NODE_NAME_COLOR = "#4C4646"
NODE_CITY_COLOR = "#D3DAE8"
NODE_FIELD_COLOR = "#EEC0E7"
NODE_ROLE_COLOR = "#F4C07C"

for _, row in filtered_df.iterrows():
    name = row["name"].strip()
    city = row["city"].strip()
    country = row["country"].strip()
    location = f"{country}, {city}" if city else country
    fields = [f.strip() for f in row["professional field"].split(",") if f.strip()]
    roles = [r.strip() for r in row["role"].split(",") if r.strip()]
    telegram = row["telegram nickname"].strip()
    email = row["email"].strip()
    photo = row["photo url"].strip()

    info = name
    if telegram:
        info += f"\nTelegram: {telegram}"
    if email:
        info += f"\nEmail: {email}"

    net.add_node(name, label=name, title=info, color=NODE_NAME_COLOR, shape="dot", size=20)
    if location:
        net.add_node(location, label=location, title=location, color=NODE_CITY_COLOR, shape="dot", size=15)
        net.add_edge(name, location)
    for field in fields:
        net.add_node(field, label=field, title=field, color=NODE_FIELD_COLOR, shape="dot", size=15)
        net.add_edge(name, field)
    for role in roles:
        net.add_node(role, label=role, title=role, color=NODE_ROLE_COLOR, shape="dot", size=15)
        net.add_edge(name, role)

net.set_options(json.dumps({
  "edges": {
    "color": {
      "color": "#4C4646",
      "highlight": "#B3A0EB",
      "inherit": False,
      "opacity": 0.8
    },
    "width": 1,
    "selectionWidth": 3,
    "hoverWidth": 1.5,
    "smooth": {
      "enabled": True,
      "type": "dynamic"
    }
  },
  "interaction": {
    "hover": True,
    "multiselect": True,
    "selectable": True,
    "selectConnectedEdges": True,
    "dragNodes": True,
    "dragView": True,
    "zoomView": True,
    "navigationButtons": False,
    "tooltipDelay": 100
  },
  "nodes": {
    "shape": "dot",
    "font": {
      "color": "#E8DED3",
      "face": "inter",
      "size": 16
    },
    "opacity": 1.0
  },
  "manipulation": False,
  "physics": {
    "enabled": True
  },
  "layout": {
    "randomSeed": 42,
    "improvedLayout": True,
    "hierarchical": {
      "enabled": False,
      "levelSeparation": 10,
      "nodeSpacing": 5,
      "treeSpacing": 10,
      "direction": "UD",
      "sortMethod": "hubsize"
    }
  }
}))

# === Генерация HTML и отображение ===
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
net.save_graph(temp_file.name)

if os.path.exists(temp_file.name):
    with open(temp_file.name, "r", encoding="utf-8") as f:
        html_code = f.read()
    st.components.v1.html(html_code, height=900)
else:
    st.error("Graph file was not created.")
