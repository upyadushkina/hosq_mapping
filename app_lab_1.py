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
GRAPH_LABEL_COLOR = "#E8DED3"          # цвет подписей узлов графа

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

# === Преобразование Google Drive ссылок ===
def convert_drive_url(url):
    if "drive.google.com" in url and "/file/d/" in url:
        try:
            file_id = url.split("/file/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        except IndexError:
            return url
    return url

# Распарсим страну и город из 'country and city'
df["country"] = df["country and city"].apply(lambda x: x.split(",")[0].strip() if "," in x else x.strip())
df["city"] = df["country and city"].apply(lambda x: x.split(",")[1].strip() if "," in x else "")

# === Фильтры ===
all_fields = sorted(set(
    field.strip()
    for sublist in df["professional field"].dropna().str.split(",")
    for field in sublist if field.strip()
))
all_roles = sorted(set(
    role.strip()
    for sublist in df["role"].dropna().astype(str).str.split(",")
    for role in sublist if role.strip()
))
all_countries = sorted(df["country"].unique().tolist())
all_cities = sorted(set(df["city"].dropna().tolist()) - {""})

st.sidebar.header("Filters")
selected_fields = st.sidebar.multiselect("Filter by Field", all_fields)
selected_roles = st.sidebar.multiselect("Filter by Role", all_roles)
selected_countries = st.sidebar.multiselect("Filter by Country", all_countries)
selected_cities = st.sidebar.multiselect("Filter by City", all_cities)

if st.sidebar.button("Clear filters"):
    selected_fields = []
    selected_roles = []
    selected_countries = []
    selected_cities = []
    selected_countries = []
    selected_cities = []
    selected_fields = []

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
NODE_ROLE_COLOR = "#F4C07C"
net = Network(height="900px", width="100%", bgcolor=PAGE_BG_COLOR, font_color=PAGE_TEXT_COLOR)

NODE_NAME_COLOR = "#4C4646"
NODE_CITY_COLOR = "#D3DAE8"
NODE_FIELD_COLOR = "#EEC0E7"

for _, row in filtered_df.iterrows():
    name = row["name"].strip()
    city = row["city"].strip()
    country = row["country"].strip()
    location = f"{country}, {city}" if city else country
    fields = [f.strip() for f in row["professional field"].split(",") if f.strip()]
    telegram = row["telegram nickname"].strip()
    email = row["email"].strip()

    info = f"<b>{name}</b>"
    if row["photo"]:
        photo_url = convert_drive_url(row["photo"].strip())
        info += f"<br><img src='{photo_url}' width='100' style='border-radius: 8px;'>"
    if telegram:
        info += f"<br><b>Telegram:</b> {telegram}"
    if email:
        info += f"<br><b>Email:</b> {email}"
    net.add_node(name, label=name, title=info, color=NODE_NAME_COLOR, shape="dot", size=35)
    if location:
        net.add_node(location, label=location, title=location, color=NODE_CITY_COLOR, shape="dot", size=18)
        net.add_edge(name, location)
    for field in fields:
        net.add_node(field, label=field, title=field, color=NODE_FIELD_COLOR, shape="dot", size=18)
        net.add_edge(name, field)

    roles = [r.strip() for r in str(row["role"]).split(",") if r.strip()]
    for role in roles:
        net.add_node(role, label=role, title=role, color=NODE_ROLE_COLOR, shape="dot", size=18)
        net.add_edge(name, role)

net.set_options(json.dumps({
  "edges": {
    "color": {
      "color": "#4C4646",
      "highlight": "#B3A0EB",
      "inherit": False,
      "opacity": 0.8
    },
    "width": 0.5,
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
    "enabled": False
  },
  "layout": {
    "randomSeed": 42,
    "improvedLayout": True,
    "hierarchical": {
      "enabled": False,
      "levelSeparation": 25,
      "nodeSpacing": 15,
      "treeSpacing": 30,
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
