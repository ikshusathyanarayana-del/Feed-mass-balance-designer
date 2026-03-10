import streamlit as st
import graphviz
import pandas as pd
import os

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Universal WtE Plant Builder", layout="wide")
st.title("⚙️ Universal Modular Waste-to-Energy Plant Builder")
st.markdown("Dynamically configure any plant architecture in the world. Select your modules, set your efficiencies, and the thermodynamic engine will route the mass balance automatically.")

# ==========================================
# UI: UNIVERSAL PLANT CONFIGURATOR
# ==========================================
st.sidebar.header("1. Plant Capacity & Baseline")
capacity_tpd = st.sidebar.number_input("Total Plant Intake (TPD)", min_value=10, max_value=10000, value=500, step=50)

st.sidebar.header("2. Build Your Architecture")
st.sidebar.markdown("*(Select the modules that exist in this specific plant)*")

# The Universal Module Selector
active_modules = st.sidebar.multiselect(
    "Active Process Modules",
    options=[
        'Bag Opener (Leachate Drain)',
        'Magnetic Separator (Ferrous)',
        'Eddy Current (Non-Ferrous)',
        'Trommel Screen (Organics)',
        'Screw Press (Wet/Dry Split)',
        'Manual Sorting (Inerts)',
        'NIR Optical (Plastics)'
    ],
    default=[
        'Bag Opener (Leachate Drain)',
        'Magnetic Separator (Ferrous)',
        'Trommel Screen (Organics)',
        'NIR Optical (Plastics)'
    ]
)

st.sidebar.markdown("*(Select the final energy recovery and disposal destinations)*")
active_destinations = st.sidebar.multiselect(
    "Downstream Energy / Disposal",
    options=['Anaerobic Digestion (AD)', 'Pyrolysis', 'WtE Incinerator', 'Sanitary Landfill'],
    default=['Anaerobic Digestion (AD)', 'WtE Incinerator']
)

# --- EXPANDER 3: COMPOSITION ---
with st.sidebar.expander("📊 3. Municipal Waste Composition (%)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        food_waste = st.number_input("Food/Organic", value=45.0, step=0.1)
        plastics = st.number_input("Plastics", value=15.0, step=0.1)
        paper = st.number_input("Paper & Cardboard", value=10.0, step=0.1)
        textile = st.number_input("Textiles", value=5.0, step=0.1)
    with col2:
        inerts_nf = st.number_input("Inerts (Glass/Stone)", value=5.0, step=0.1)
        ferrous = st.number_input("Ferrous Metals", value=2.0, step=0.1)
        non_ferrous = st.number_input("Non-Ferrous Metals", value=1.0, step=0.1)
        others_residual = st.number_input("Other Residuals", value=17.0, step=0.1)

# --- EXPANDER 4: MACHINE EFFICIENCIES ---
with st.sidebar.expander("⚙️ 4. Machine Efficiencies (%)", expanded=False):
    eff_bag_leachate = st.slider("Leachate Moisture Drain (%)", 0, 30, 15) if 'Bag Opener (Leachate Drain)' in active_modules else 0
    eff_mag = st.slider("Magnetic Sep (Ferrous Extraction)", 0, 100, 90) if 'Magnetic Separator (Ferrous)' in active_modules else 0
    eff_eddy = st.slider("Eddy Current (Non-Ferrous Ext.)", 0, 100, 85) if 'Eddy Current (Non-Ferrous)' in active_modules else 0
    eff_trommel = st.slider("Trommel (Organics Extraction)", 0, 100, 80) if 'Trommel Screen (Organics)' in active_modules else 0
    screw_press_solid = st.slider("Screw Press (Solid Fraction % to WtE)", 0, 100, 40) if 'Screw Press (Wet/Dry Split)' in active_modules else 0
    eff_manual = st.slider("Manual Sorting (Inerts Ext.)", 0, 100, 95) if 'Manual Sorting (Inerts)' in active_modules else 0
    eff_nir = st.slider("NIR Sorter (Plastics Extraction)", 0, 100, 85) if 'NIR Optical (Plastics)' in active_modules else 0

# --- EXPANDER 5: CV DATA ---
with st.sidebar.expander("🔥 5. Calorific Values (Kcal/kg)", expanded=False):
    cv_plastics = st.number_input("Plastics CV", value=3300, step=100)
    cv_org_dry = st.number_input("Dry Organics CV", value=2629, step=10)
    cv_residual = st.number_input("General Residual CV", value=2500, step=100)

# ==========================================
# UNIVERSAL MASS BALANCE ENGINE
# ==========================================
# Normalize composition just in case
total_comp = food_waste + plastics + paper + textile + inerts_nf + ferrous + non_ferrous + others_residual
f_w = food_waste / total_comp
p_w = plastics / total_comp
i_w = inerts_nf / total_comp
fe_w = ferrous / total_comp
nf_w = non_ferrous / total_comp
res_pct = (paper + textile + others_residual) / total_comp

def run_universal_mass_balance():
    DAYS_PER_YEAR = 330
    dot = graphviz.Digraph(comment='Universal Mass Balance', format='png')
    dot.attr(rankdir='TB', nodesep='0.6', ranksep='0.8')
    dot.attr('node', shape='none', fontname='Helvetica', fontsize='9')
    mass_balance_data = []

    def make_mb_node(node_id, title, bgcolor, tpd):
        if tpd < 0.01: return 0
        pct_total = (tpd / capacity_tpd) * 100.0
        tpy = tpd * DAYS_PER_YEAR
        mass_balance_data.append({"Process Node": title, "Tons/Day": round(tpd, 2), "Tons/Year": round(tpy, 0), "% of Total": f"{pct_total:.2f}%"})
        html = f"""<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
            <TR><TD COLSPAN="2" BGCOLOR="{bgcolor}"><B>{title}</B></TD></TR>
            <TR><TD>{pct_total:.2f}%</TD><TD>{tpy:,.0f} Tons/Year</TD></TR>
            <TR><TD>330 Days/Year</TD><TD>{tpd:,.2f} Tons/Day</TD></TR></TABLE>>"""
        dot.node(node_id, html)
        return tpd

    def make_process_node(node_id, label, color, shape='box'):
        dot.node(node_id, label, shape=shape, style='filled', fillcolor=color, fontname='Helvetica', fontsize='10')

    curr_tpd = capacity_tpd
    make_mb_node('Reception', '1. RECEPTION OF MATERIAL', '#c5e0b4', curr_tpd)
    spine = 'Reception'

    # Track extracted materials for downstream routing
    extracted_ad = 0
    extracted_dry_org = 0
    extracted_plas = 0

    # ---------------------------------------------------------
    # DYNAMIC PIPELINE ROUTING
    # ---------------------------------------------------------
    if 'Bag Opener (Leachate Drain)' in active_modules:
        make_mb_node('BagOpener', 'BAG OPENER & DRAIN', '#e2efda', curr_tpd)
        dot.edge(spine, 'BagOpener', color='#4f81bd', penwidth='3')
        spine = 'BagOpener'
        leachate_tpd = capacity_tpd * (eff_bag_leachate / 100.0)
        if leachate_tpd > 0:
            make_mb_node('Leachate', 'WASTEWATER / LEACHATE', '#9bc2e6', leachate_tpd)
            dot.edge(spine, 'Leachate', color='#4f81bd', penwidth='2')
            curr_tpd -= leachate_tpd

    if 'Magnetic Separator (Ferrous)' in active_modules:
        make_mb_node('MagSep', 'MAGNETIC SEPARATOR', '#ccc1da', curr_tpd)
        dot.edge(spine, 'MagSep', color='#4f81bd', penwidth='3')
        spine = 'MagSep'
        ferrous_tpd = (capacity_tpd * fe_w) * (eff_mag / 100.0)
        if ferrous_tpd > 0:
            make_mb_node('Ferrous', 'RECOVERED FERROUS', '#f8cbad', ferrous_tpd)
            dot.edge(spine, 'Ferrous', color='#4f81bd', penwidth='2')
            curr_tpd -= ferrous_tpd

    if 'Eddy Current (Non-Ferrous)' in active_modules:
        make_mb_node('Eddy', 'EDDY CURRENT SEPARATOR', '#ccc1da', curr_tpd)
        dot.edge(spine, 'Eddy', color='#4f81bd', penwidth='3')
        spine = 'Eddy'
        nf_tpd = (capacity_tpd * nf_w) * (eff_eddy / 100.0)
        if nf_tpd > 0:
            make_mb_node('NonFerrous', 'RECOVERED NON-FERROUS', '#f8cbad', nf_tpd)
            dot.edge(spine, 'NonFerrous', color='#4f81bd', penwidth='2')
            curr_tpd -= nf_tpd

    if 'Trommel Screen (Organics)' in active_modules:
        make_mb_node('Trommel', 'TROMMEL SCREEN', '#e2efda', curr_tpd)
        dot.edge(spine, 'Trommel', color='#4f81bd', penwidth='3')
        spine = 'Trommel'
        org_extracted = (capacity_tpd * f_w) * (eff_trommel / 100.0)
        
        if org_extracted > 0:
            curr_tpd -= org_extracted
            if 'Screw Press (Wet/Dry Split)' in active_modules:
                make_mb_node('ScrewPress', 'ORGANICS SCREW PRESS', '#ffe699', org_extracted)
                dot.edge(spine, 'ScrewPress', color='#4f81bd', penwidth='2')
                extracted_dry_org = org_extracted * (screw_press_solid / 100.0)
                extracted_ad = org_extracted - extracted_dry_org
                make_mb_node('WetOrg', 'WET ORGANICS (LIQUID)', '#9bc2e6', extracted_ad)
                dot.edge('ScrewPress', 'WetOrg', color='blue', penwidth='1')
                make_mb_node('DryOrg', 'DRY ORGANICS', '#f8cbad', extracted_dry_org)
                dot.edge('ScrewPress', 'DryOrg', color='orange', penwidth='1')
            else:
                extracted_ad = org_extracted
                make_mb_node('WetOrg', 'EXTRACTED ORGANICS', '#f8cbad', extracted_ad)
                dot.edge(spine, 'WetOrg', color='#4f81bd', penwidth='2')

    if 'Manual Sorting (Inerts)' in active_modules:
        make_mb_node('ManualSort', 'MANUAL SORTING', '#fce4d6', curr_tpd)
        dot.edge(spine, 'ManualSort', color='#4f81bd', penwidth='3')
        spine = 'ManualSort'
        inerts_tpd = (capacity_tpd * i_w) * (eff_manual / 100.0)
        if inerts_tpd > 0:
            make_mb_node('Inerts', 'REJECTS / INERTS', '#f8cbad', inerts_tpd)
            dot.edge(spine, 'Inerts', color='#4f81bd', penwidth='2')
            curr_tpd -= inerts_tpd

    if 'NIR Optical (Plastics)' in active_modules:
        make_mb_node('NIR', 'NIR OPTICAL SORTER', '#fff2cc', curr_tpd)
        dot.edge(spine, 'NIR', color='#4f81bd', penwidth='3')
        spine = 'NIR'
        extracted_plas = (capacity_tpd * p_w) * (eff_nir / 100.0)
        if extracted_plas > 0:
            make_mb_node('Plastics', 'RECOVERED PLASTICS', '#f8cbad', extracted_plas)
            dot.edge(spine, 'Plastics', color='#4f81bd', penwidth='2')
            curr_tpd -= extracted_plas

    # ---------------------------------------------------------
    # DOWNSTREAM DESTINATION ROUTING
    # ---------------------------------------------------------
    final_residual_tpd = curr_tpd

    if 'Anaerobic Digestion (AD)' in active_destinations and extracted_ad > 0:
        make_process_node('AD_Plant', 'Anaerobic Digester\n(Biogas Plant)', '#98FB98')
        dot.edge('WetOrg', 'AD_Plant', penwidth='2')
    elif extracted_ad > 0:
        # If no AD exists, organics go to landfill or compost
        make_process_node('Compost', 'Composting / Landfill', '#D3D3D3')
        dot.edge('WetOrg', 'Compost', style='dashed')

    if 'Pyrolysis' in active_destinations and extracted_plas > 0:
        make_process_node('Pyro_Plant', 'Pyrolysis Reactor\n(Synthetic Fuel)', '#DDA0DD')
        dot.edge('Plastics', 'Pyro_Plant', penwidth='2')
    elif extracted_plas > 0:
        # If no pyro exists, plastics are sold as bales
        make_process_node('Baler', 'Plastic Baling for Sale', '#D3D3D3')
        dot.edge('Plastics', 'Baler', style='dashed')

    final_wte_feed = 0
    total_kcal = 0
    wte_energy_data = []

    if 'WtE Incinerator' in active_destinations:
        final_wte_feed = final_residual_tpd + extracted_dry_org
        make_mb_node('WtE', 'WtE INCINERATOR', '#a9d18e', final_wte_feed)
        dot.edge(spine, 'WtE', label='General Residuals', color='#4f81bd', penwidth='4')
        if extracted_dry_org > 0:
            dot.edge('DryOrg', 'WtE', label='Dry Organics', color='orange', style='dashed', penwidth='2')
        
        make_process_node('Turbine', 'Steam Turbine', '#FFD700')
        dot.edge('WtE', 'Turbine', color='blue')

        # Calorific Math
        wte_energy_data.append({"Material": "General Residuals", "Tons/Day": round(final_residual_tpd, 2), "CV (Kcal/kg)": cv_residual})
        total_kcal += final_residual_tpd * cv_residual
        if extracted_dry_org > 0:
            wte_energy_data.append({"Material": "Dry Organics", "Tons/Day": round(extracted_dry_org, 2), "CV (Kcal/kg)": cv_org_dry})
            total_kcal += extracted_dry_org * cv_org_dry

    elif 'Sanitary Landfill' in active_destinations:
        final_wte_feed = final_residual_tpd + extracted_dry_org
        make_mb_node('Landfill', 'SANITARY LANDFILL', '#A9A9A9', final_wte_feed)
        dot.edge(spine, 'Landfill', label='Residual Waste', color='#4f81bd', penwidth='4')
        if extracted_dry_org > 0:
            dot.edge('DryOrg', 'Landfill', color='orange', style='dashed', penwidth='2')

    avg_cv_kcal = (total_kcal / final_wte_feed) if final_wte_feed > 0 else 0
    avg_cv_mj = avg_cv_kcal * 0.004184

    return dot, mass_balance_data, wte_energy_data, avg_cv_kcal, avg_cv_mj, final_wte_feed, extracted_ad, extracted_plas

diagram, mb_data, wte_data, avg_cv_kcal, avg_cv_mj, final_wte_feed, extracted_ad, extracted_plas = run_universal_mass_balance()

# ==========================================
# UI: DISPLAY DASHBOARD
# ==========================================
st.subheader("Process Flow & Dynamic Mass Balance")
st.graphviz_chart(diagram, use_container_width=True)
st.divider()

colA, colB, colC = st.columns(3)
if 'WtE Incinerator' in active_destinations:
    colA.metric("Total Feed to Incinerator", f"{final_wte_feed:.2f} TPD")
    colB.metric("Average Feed CV (Kcal/kg)", f"{avg_cv_kcal:,.0f} Kcal/kg")
    colC.metric("Average Feed CV (MJ/kg)", f"{avg_cv_mj:.2f} MJ/kg")
else:
    colA.metric("Total Waste to Landfill", f"{final_wte_feed:.2f} TPD")
    colB.metric("Organics Diverted", f"{extracted_ad:.2f} TPD")
    colC.metric("Plastics Diverted", f"{extracted_plas:.2f} TPD")

col_table1, col_table2 = st.columns(2)
with col_table1:
    if len(wte_data) > 0:
        st.markdown("**Burnable Residual Makeup**")
        st.dataframe(pd.DataFrame(wte_data), use_container_width=True)
    else:
        st.info("WtE Incinerator is turned off. No CV analysis required.")
with col_table2:
    st.markdown("**Overall Mass Balance Data**")
    st.dataframe(pd.DataFrame(mb_data), use_container_width=True)
