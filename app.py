import streamlit as st
import graphviz
import pandas as pd
import os

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Dynamic FEED Designer", layout="wide")
st.title("⚙️ Dynamic Waste-to-Energy Plant Designer")
st.markdown("Clean mass balance routing with downstream process systems, an interactive Calorific Value (CV) toggle, and Environmental Impact modeling.")

# ==========================================
# UI: SIDEBAR INPUTS (ISABELA DEFAULTS)
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)
else:
    st.sidebar.markdown("*(Upload a 'logo.png' or 'logo.jpg' to GitHub to display your company logo here)*")

st.sidebar.header("1. Operational Input")
capacity_tpd = st.sidebar.number_input("Plant Capacity (TPD)", min_value=10, max_value=5000, value=350, step=10)

excel_mode = st.sidebar.toggle("🧮 Match Excel CV Logic", value=True, help="Overrides standard physical math. Simulates the 50/50 organic WET/DRY split and a 15% 'Ghost Leachate' drainage to exactly match the target Excel file.")

st.sidebar.header("2. Client Preferences")
pref_tech = st.sidebar.multiselect(
    "Preferred Technology",
    options=['WtE', 'AD', 'Pyrolysis'],
    default=['WtE', 'AD', 'Pyrolysis']
)
energy_output = st.sidebar.multiselect(
    "Desired Energy Output",
    options=['Electricity', 'Biogas', 'Fuel Oil'],
    default=['Electricity', 'Biogas', 'Fuel Oil']
)

# --- EXPANDER 3: COMPOSITION ---
with st.sidebar.expander("📊 3. Waste Composition (%)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        food_waste = st.number_input("Food Waste", value=51.27, step=0.1)
        garden_waste = st.number_input("Garden Waste", value=15.89, step=0.1)
        plastics = st.number_input("Plastics", value=15.54, step=0.1)
        paper = st.number_input("Paper & Cardboard", value=6.73, step=0.1)
        textile = st.number_input("Textile", value=2.04, step=0.1)
        pampers = st.number_input("Pampers", value=4.10, step=0.1)
    with col2:
        wood = st.number_input("Wood Products", value=0.18, step=0.1)
        inerts = st.number_input("Inerts (Stones/Glass)", value=1.79, step=0.1)
        ferrous = st.number_input("Metals (Ferrous)", value=0.60, step=0.1)
        non_ferrous = st.number_input("Metals (Non-Ferrous)", value=0.38, step=0.1)
        others = st.number_input("Others Components", value=1.48, step=0.1)
        rubber = st.number_input("Rubber", value=0.00, step=0.1)

# --- EXPANDER 4: MACHINE EFFICIENCIES ---
with st.sidebar.expander("⚙️ 4. Machine Efficiencies (%)", expanded=False):
    st.markdown("*(Set to original spreadsheet defaults)*")
    eff_nir = st.slider("NIR Sorter (Plastics)", 0, 100, 50) 
    eff_trommel = st.slider("Trommel (Organics)", 0, 100, 62) 
    eff_mag = st.slider("Magnetic Sep (Ferrous)", 0, 100, 100)
    eff_manual = st.slider("Manual Sorting (Inerts & NF)", 0, 100, 100) 

# --- EXPANDER 5: MOISTURE & CV DATA ---
with st.sidebar.expander("💧 & 🔥 5. Moisture & CV Data", expanded=False):
    st.markdown("*Moisture Content (% Dry Material)*")
    dry_food = st.number_input("Food Dry %", value=15.0) / 100.0
    dry_garden = st.number_input("Garden Dry %", value=15.0) / 100.0
    dry_plastics = st.number_input("Plastics Dry %", value=100.0) / 100.0
    dry_paper = st.number_input("Paper Dry %", value=80.0) / 100.0
    dry_textile = st.number_input("Textile Dry %", value=50.0) / 100.0
    dry_pampers = st.number_input("Pampers Dry %", value=50.0) / 100.0
    dry_wood = st.number_input("Wood Dry %", value=80.0) / 100.0
    dry_inerts = st.number_input("Inerts Dry %", value=100.0) / 100.0
    dry_ferrous = st.number_input("Ferrous Dry %", value=100.0) / 100.0
    dry_non_ferrous = st.number_input("Non-Ferrous Dry %", value=100.0) / 100.0
    dry_others = st.number_input("Others Dry %", value=80.0) / 100.0
    dry_rubber = st.number_input("Rubber Dry %", value=60.0) / 100.0
    
    st.markdown("*Calorific Values (Kcal/kg)*")
    cv_paper = st.number_input("Paper & Cardboard CV", value=3585, step=100)
    cv_plastics = st.number_input("Plastics CV", value=3300, step=100)
    cv_wood = st.number_input("Wood CV", value=3100, step=100)
    cv_textile = st.number_input("Textile CV", value=3872, step=100)
    cv_pampers = st.number_input("Pampers CV", value=1
