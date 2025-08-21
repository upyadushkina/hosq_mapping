import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from collections import defaultdict
import base64

# === Color Scheme ===
PAGE_BG_COLOR = "#262123"
PAGE_TEXT_COLOR = "#E8DED3"
SIDEBAR_BG_COLOR = "#262123"
SIDEBAR_LABEL_COLOR = "#E8DED3"
SIDEBAR_TAG_TEXT_COLOR = "#E8DED3"
SIDEBAR_TAG_BG_COLOR = "#6A50FF"
BUTTON_BG_COLOR = "#262123"
BUTTON_TEXT_COLOR = "#4C4646"
BUTTON_CLEAN_TEXT_COLOR = "#E8DED3"
SIDEBAR_HEADER_COLOR = "#E8DED3"
SIDEBAR_TOGGLE_ARROW_COLOR = "#E8DED3"
HEADER_MENU_COLOR = "#262123"
GRAPH_BG_COLOR = "#262123"
GRAPH_LABEL_COLOR = "#E8DED3"
NODE_NAME_COLOR = "#4C4646"
NODE_CITY_COLOR = "#D3DAE8"
NODE_FIELD_COLOR = "#EEC0E7"
NODE_ROLE_COLOR = "#F4C07C"
EDGE_COLOR = "#322C2E"
HIGHLIGHT_EDGE_COLOR = "#6A50FF"
TEXT_FONT = "Lexend"
DEFAULT_PHOTO = "https://static.tildacdn.com/tild3532-6664-4163-b538-663866613835/hosq-design-NEW.png"
POPUP_BG_COLOR = "#262123"
POPUP_TEXT_COLOR = "#E8DED3"


def get_google_drive_image_url(url):
    if "drive.google.com" in url and "/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/thumbnail?id={file_id}"
    return url

st.set_page_config(page_title="Notations Lab", layout="wide")
st.markdown(f"""
  <style>
    html, body, .stApp, .css-18e3th9, .css-1d391kg {{
      background-color: {PAGE_BG_COLOR} !important;
      color: {PAGE_TEXT_COLOR} !important;
      font-family: '{TEXT_FONT}', sans-serif;
    }}
    header, footer {{
      font-family: '{TEXT_FONT}', sans-serif;
      background-color: {PAGE_BG_COLOR} !important;
    }}
    section[data-testid="stSidebar"] {{
      font-family: '{TEXT_FONT}', sans-serif;
      background-color: {SIDEBAR_BG_COLOR} !important;
    }}
    section[data-testid="stSidebar"] * {{
      font-family: '{TEXT_FONT}', sans-serif;
      color: {PAGE_TEXT_COLOR} !important;
    }}
    section[data-testid="stSidebar"] h1, h2, h3 {{
      font-family: '{TEXT_FONT}', sans-serif;
      color: {PAGE_TEXT_COLOR} !important;
    }}
    .stMultiSelect [data-baseweb="select"] input {{
      font-family: '{TEXT_FONT}', sans-serif;
      color: #4C4646 !important;
    }}
    .stMultiSelect [data-baseweb="tag"] {{
      background-color: {SIDEBAR_TAG_BG_COLOR} !important;
      font-family: '{TEXT_FONT}', sans-serif;
      color: {SIDEBAR_TAG_TEXT_COLOR} !important;
    }}
    .stCheckbox > label {{
      color: {PAGE_TEXT_COLOR} !important;
    }}
  </style>
""", unsafe_allow_html=True)

# Load and process CSV
df = pd.read_csv("Notations Lab DATABASE.csv")
df.fillna('', inplace=True)

category_colors = {
    'artist': NODE_NAME_COLOR,
    # 'city': "#322C2E",
    'country': "#322C2E",
    'department': "#6A50FF",
    'role': "#F4C07C",
    'discipline': "#E8DED3",
    'instruments': "#EEC0E7",
    'skill set': "#B1D3AA",
    # 'seeking for': "#EC7F4D",
}

multi_fields = ['department', 'role', 'discipline', 'instruments', 'skill set']
nodes, links, artist_info = [], [], {}
node_ids, edge_ids = set(), set()
filter_options = defaultdict(set)

artist_links_map = defaultdict(set)

def add_node(id, label, group):
    if id not in node_ids:
        nodes.append({"id": id, "label": label, "group": group, "color": category_colors.get(group, '#888888')})
        node_ids.add(id)

def add_link(source, target):
    key = f"{source}___{target}"
    if key not in edge_ids:
        links.append({"source": source, "target": target})
        edge_ids.add(key)
        if source.startswith("artist::"):
            artist_links_map[source].add(target)
        elif target.startswith("artist::"):
            artist_links_map[target].add(source)

for _, row in df.iterrows():
    artist_id = f"artist::{row['name']}"
    add_node(artist_id, row['name'], 'artist')

    photo_url = get_google_drive_image_url(row['photo url']) if row['photo url'] else DEFAULT_PHOTO

    # country = ''
    # city = ''
    # if row['country and city']:
    #    parts = [p.strip() for p in row['country and city'].split(',')]
    #    if len(parts) == 2:
    #        country, city = parts

    # def clean_text(text):
    # if not isinstance(text, str):
    #     return text
    # return (
    #     text.replace("&", "&amp;")
    #         .replace("<", "&lt;")
    #         .replace(">", "&gt;")
    #         .replace('"', "&quot;")
    #         .replace("'", "&#39;")
    #         .replace("@", "&#64;")
    # )

    # artist_info[artist_id] = {
    # "name": clean_text(row['name']),
    # "photo": photo_url,
    # "telegram": clean_text(row["telegram nickname"]),
    # "email": clean_text(row["email"]),
    # "country": clean_text(row['country and city']),
    # "role": clean_text(row['role']),
    # "discipline": clean_text(row['discipline']),
    # "department": clean_text(row['department']),
    # "instruments": clean_text(row['instruments']),
    # "skill set": clean_text(row['skill set'])
    # }

    def clean_text(text):
        return text.replace('@', '&#64;') if isinstance(text, str) else text

    artist_info[artist_id] = {
        "name": row['name'],
        "photo": photo_url,
        "telegram": clean_text(row["telegram nickname"]),
        "email": clean_text(row["email"]),
        "country": row['country and city'],
        # "city": city,
        "role": row['role'],
        "discipline": row['discipline'],
        "department": row['department'],
        "instruments": row['instruments'],
        "skill set": row['skill set']
    }


    for field in multi_fields:
        values = [v.strip() for v in row[field].split(',')] if row[field] else []
        for val in values:
            if val:
                node_id = f"{field}::{val}"
                add_node(node_id, val, field)
                add_link(artist_id, node_id)
                filter_options[field].add(val)

    # if row['country and city']:
    #     parts = [p.strip() for p in row['country and city'].split(',')]
    #     if len(parts) == 2:
    #         country, city = parts
    #         country_id = f"country::{country}"
    #         city_id = f"city::{city}"
    #         add_node(country_id, country, 'country')
    #         add_node(city_id, city, 'city')
    #         add_link(artist_id, city_id)
    #         add_link(artist_id, country_id)
    #         add_link(city_id, country_id)
    #         filter_options['country'].add(country)
    #         filter_options['city'].add(city)

# Sidebar filters
selected = {}
st.sidebar.header("Filters")
for category, options in filter_options.items():
    if category == "role":
        st.sidebar.subheader("Role")
    # elif category == "level":
    #    st.sidebar.subheader("Level")
    # elif category == "seeking for":
    #     st.sidebar.subheader("You can choose the artists who is seeking for...")
    # if category in ["level", "role"]:
    if category in ["level", "role"]:
        selected[category] = [val for val in sorted(options) if st.sidebar.checkbox(val, key=f"{category}_{val}")]
    else:
        selected[category] = st.sidebar.multiselect(
            label=category.title(),
            options=sorted(options),
            default=[]
        )

def artist_passes_filter(artist_id):
    for cat, selected_vals in selected.items():
        if not selected_vals:
            continue
        relevant = {f"{cat}::{val}" for val in selected_vals}
        if not artist_links_map[artist_id].intersection(relevant):
            return False
    return True

visible_artist_ids = {a for a in artist_info if artist_passes_filter(a)}
visible_related_ids = set(visible_artist_ids)

for link in links:
    if link["source"] in visible_artist_ids:
        visible_related_ids.add(link["target"])
    if link["target"] in visible_artist_ids:
        visible_related_ids.add(link["source"])

visible_nodes = [n for n in nodes if n["id"] in visible_related_ids]
visible_links = [l for l in links if l["source"] in visible_related_ids and l["target"] in visible_related_ids]

d3_data = {
    "nodes": visible_nodes,
    "links": visible_links,
    "artists": artist_info
}

d3_json = json.dumps(d3_data)
b64_data = base64.b64encode(d3_json.encode("utf-8")).decode("utf-8")

with open("graph_template.html", "r", encoding="utf-8") as f:
    html_template = f.read()

html_filled = html_template.replace("{{ b64_data }}", b64_data)
html_filled = html_filled.replace("{{ popup_bg }}", POPUP_BG_COLOR)
html_filled = html_filled.replace("{{ popup_text }}", POPUP_TEXT_COLOR)

components.html(html_filled, height=1400, scrolling=False)
