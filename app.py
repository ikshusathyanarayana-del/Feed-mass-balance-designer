import streamlit as st
import graphviz
import pandas as pd
import os

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Dynamic FEED Designer", layout="wide")
st.title("⚙️ Dynamic Waste-to-Energy Plant Designer (3MW R3 Architecture)")
st.markdown("Advanced Mass Balance routing featuring early Leachate extraction, Organics Screw Press separation, and dynamic RDF blending.")

# ==========================================
# UI: SIDEBAR INPUTS (3MW PUERTO PRINCESA DEFAULTS)
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.markdown("*(Upload 'logo.png' to display company logo)*")

st.sidebar.header("1. Operational Input")
capacity_tpd = st.sidebar.number_input("Plant Capacity (TPD)", min_value=10, max_value=5000, value=300, step=10)

st.sidebar.header("2. Client Preferences")
pref_tech = st.sidebar.multiselect(
    "Preferred Technology",
    options=['WtE / RDF', 'AD / LTP', 'Pyrolysis'],
    default=['WtE / RDF', 'AD / LTP', 'Pyrolysis']
)

# --- EXPANDER 3: COMPOSITION ---
with st.sidebar.expander("📊 3. Waste Composition (%)", expanded=False):
    st.info("Defaults matched to R3 Mass Balance PDF.")
    col1, col2 = st.columns(2)
    with col1:
        food_waste = st.number_input("Food/Organic", value=20.13, step=0.1)
        plastics = st.number_input("Plastics", value=19.69, step=0.1)
        bulky = st.number_input("Bulky Materials", value=1.00, step=0.1)
        inerts_nf = st.number_input("Inerts & Non-Ferrous", value=1.72, step=0.1)
    with col2:
        ferrous = st.number_input("Ferrous Metals", value=1.10, step=0.1)
        others_residual = st.number_input("Residual / Paper / Textile", value=56.36, step=0.1)

# --- EXPANDER 4: MACHINE EFFICIENCIES ---
with st.sidebar.expander("⚙️ 4. Machine Efficiencies (%)", expanded=False):
    st.markdown("*(Controls how much target material is successfully extracted)*")
    eff_bag_leachate = st.slider("Bag Opener Leachate Drain (%)", 0, 30, 15)
    eff_mag = st.slider("Magnetic Sep (Ferrous)", 0, 100, 100)
    eff_trommel = st.slider("Trommel (Organics)", 0, 100, 100)
    screw_press_solid = st.slider("Screw Press Solid Yield (%)", 0, 100, 40, help="Percentage of Organics sent as dry matter to RDF. The rest becomes liquid for LTP/AD.")
    eff_manual = st.slider("Manual Sorting (Inerts & NF)", 0, 100, 100) 
    eff_nir = st.slider("NIR Sorter (Plastics)", 0, 100, 100) 

# --- EXPANDER 5: MOISTURE & CV DATA ---
with st.sidebar.expander("💧 & 🔥 5. Moisture & CV Data", expanded=False):
    cv_plastics = st.number_input("Plastics CV", value=3300, step=100)
    cv_org_dry = st.number_input("Organics - DRY CV", value=2629, step=10)
    cv_residual = st.number_input("Residuals CV", value=3585, step=100)

# ==========================================
# DATA COMPILATION & MASS BALANCE ENGINE
# ==========================================
# Normalize composition just in case
total_comp = food_waste + plastics + bulky + inerts_nf + ferrous + others_residual
f_w = food_waste / total_comp
p_w = plastics / total_comp
b_w = bulky / total_comp
i_w = inerts_nf / total_comp
fe_w = ferrous / total_comp
r_w = others_residual / total_comp

def run_mass_balance():
    DAYS_PER_YEAR = 330
    
    dot = graphviz.Digraph(comment='R3 Architecture Mass Balance', format='png')
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

    # 1. RECEPTION
    curr_tpd = capacity_tpd
    make_mb_node('Reception', 'RECEPTION OF MATERIAL (HOPPER)', '#c5e0b4', curr_tpd)
    spine = 'Reception'

    # 2. BAG OPENER
    make_mb_node('BagOpener', 'BAG OPENER', '#e2efda', curr_tpd)
    dot.edge(spine, 'BagOpener', color='#4f81bd', penwidth='3')
    spine = 'BagOpener'
    
    # Extract Bulky
    bulky_tpd = curr_tpd * b_w
    if bulky_tpd > 0:
        make_mb_node('Bulky', 'BULKY MATERIALS', '#f8cbad', bulky_tpd)
        dot.edge(spine, 'Bulky', color='#4f81bd', penwidth='2')
        curr_tpd -= bulky_tpd
        
    # Extract Leachate
    leachate_tpd = capacity_tpd * (eff_bag_leachate / 100.0)
    if leachate_tpd > 0:
        make_mb_node('Leachate', 'LEACHATE', '#9bc2e6', leachate_tpd)
        dot.edge(spine, 'Leachate', color='#4f81bd', penwidth='2')
        curr_tpd -= leachate_tpd

    # 3. MAGNETIC SEPARATOR
    make_mb_node('MagSep', 'MAGNETIC SEPARATOR', '#ccc1da', curr_tpd)
    dot.edge(spine, 'MagSep', color='#4f81bd', penwidth='3')
    spine = 'MagSep'
    
    ferrous_tpd = (capacity_tpd * fe_w) * (eff_mag / 100.0)
    if ferrous_tpd > 0:
        make_mb_node('Ferrous', 'FERROUS MATERIAL', '#f8cbad', ferrous_tpd)
        dot.edge(spine, 'Ferrous', color='#4f81bd', penwidth='2')
        curr_tpd -= ferrous_tpd

    # 4. TROMMEL SCREEN (ORGANICS)
    make_mb_node('Trommel', 'SPLITTER / TROMMEL', '#e2efda', curr_tpd)
    dot.edge(spine, 'Trommel', color='#4f81bd', penwidth='3')
    spine = 'Trommel'
    
    org_extracted = (capacity_tpd * f_w) * (eff_trommel / 100.0)
    ad_tpd_total = 0
    dry_org_rdf = 0
    if org_extracted > 0:
        make_mb_node('Organics', 'ORGANICS', '#f8cbad', org_extracted)
        dot.edge(spine, 'Organics', color='#4f81bd', penwidth='2')
        curr_tpd -= org_extracted
        
        # 4a. SCREW PRESS
        make_mb_node('ScrewPress', 'ORGANICS - SCREW PRESS', '#ffe699', org_extracted)
        dot.edge('Organics', 'ScrewPress', color='#4f81bd', penwidth='2')
        
        dry_org_rdf = org_extracted * (screw_press_solid / 100.0)
        wet_org_ltp = org_extracted - dry_org_rdf
        ad_tpd_total = wet_org_ltp
        
        make_mb_node('LTP', 'LTP / AD MAKE-UP LIQUID', '#9bc2e6', wet_org_ltp)
        dot.edge('ScrewPress', 'LTP', color='blue', penwidth='1')
        make_mb_node('DryOrg', 'DRY MATERIAL TO RDF', '#f8cbad', dry_org_rdf)
        dot.edge('ScrewPress', 'DryOrg', color='orange', penwidth='1')

    # 5. MANUAL SORTING & SDS
    make_mb_node('ManualSort', 'MANUAL SORTING STATION & SDS', '#fce4d6', curr_tpd)
    dot.edge(spine, 'ManualSort', color='#4f81bd', penwidth='3')
    spine = 'ManualSort'
    
    inerts_tpd = (capacity_tpd * i_w) * (eff_manual / 100.0)
    if inerts_tpd > 0:
        make_mb_node('Inerts', 'INERTS & NON-FERROUS REJECTS', '#f8cbad', inerts_tpd)
        dot.edge(spine, 'Inerts', color='#4f81bd', penwidth='2')
        curr_tpd -= inerts_tpd

    # 6. NIR OPTICAL SORTING (PLASTICS)
    make_mb_node('NIR', 'NIR (OPTICAL SORTING)', '#fff2cc', curr_tpd)
    dot.edge(spine, 'NIR', color='#4f81bd', penwidth='3')
    spine = 'NIR'
    
    plas_tpd = (capacity_tpd * p_w) * (eff_nir / 100.0)
    if plas_tpd > 0:
        make_mb_node('Plastics', 'PLASTICS TO PYRO PLANT', '#f8cbad', plas_tpd)
        dot.edge(spine, 'Plastics', color='#4f81bd', penwidth='2')
        curr_tpd -= plas_tpd

    # 7. RDF / WtE PLANT
    final_wte_tpd = curr_tpd + dry_org_rdf
    make_mb_node('RDF', 'RDF / WtE PLANT', '#a9d18e', final_wte_tpd)
    dot.edge(spine, 'RDF', label='Residual', color='#4f81bd', penwidth='4')
    if dry_org_rdf > 0:
        dot.edge('DryOrg', 'RDF', label='Dry Organics', color='orange', style='dashed', penwidth='2')

    # Energy Data calculation
    wte_energy_data = [
        {"Material": "Dry Organics from Screw Press", "Tons/Day": round(dry_org_rdf, 2), "CV (Kcal/kg)": cv_org_dry},
        {"Material": "Residual / Paper / Textiles", "Tons/Day": round(curr_tpd, 2), "CV (Kcal/kg)": cv_residual}
    ]
    total_kcal = (dry_org_rdf * cv_org_dry) + (curr_tpd * cv_residual)
    avg_cv_kcal = (total_kcal / final_wte_tpd) if final_wte_tpd > 0 else 0
    avg_cv_mj = avg_cv_kcal * 0.004184

    return dot, mass_balance_data, wte_energy_data, avg_cv_kcal, avg_cv_mj, final_wte_tpd, ad_tpd_total, plas_tpd

diagram, mb_data, wte_data, avg_cv_kcal, avg_cv_mj, final_wte_tpd, ad_tpd_total, plas_tpd = run_mass_balance()

# ==========================================
# UI: TABS LAYOUT
# ==========================================
tab1, tab2 = st.tabs(["📊 Mass Balance R3 Flow", "🌍 Environmental & CO2e Impact"])

with tab1:
    st.subheader("Process Flow & Dynamic Mass Balance (3MW R3 Design)")
    st.graphviz_chart(diagram, use_container_width=True)
    st.divider()
    
    colA, colB, colC = st.columns(3)
    colA.metric("Total RDF to WtE", f"{final_wte_tpd:.2f} TPD")
    colB.metric("Average RDF CV (Kcal/kg)", f"{avg_cv_kcal:,.0f} Kcal/kg")
    colC.metric("Average RDF CV (MJ/kg)", f"{avg_cv_mj:.2f} MJ/kg")

    col_table1, col_table2 = st.columns(2)
    with col_table1:
        st.markdown("**WtE Residual Makeup**")
        st.dataframe(pd.DataFrame(wte_data), use_container_width=True)
    with col_table2:
        st.markdown("**Overall Mass Balance Data**")
        df_mb = pd.DataFrame(mb_data)
        st.dataframe(df_mb, use_container_width=True)

with tab2:
    st.subheader("🌍 Environmental & CO2e Reduction Models")
    
    # Excels Mode is no longer needed to "hack" the leachate, but we retain it for flat-multiplier comparison
    match_excel_co2 = st.toggle("🧮 Match Excel CO2 Logic", value=True, help="Applies flat multipliers from legacy spreadsheets (365 days, 0 grid offsets).")

    if match_excel_co2:
        st.warning("⚠️ **Excel Mode is ON:** Calculating emissions using legacy flat-multiplier formulas (365 days/year, NO grid offsets).")
        
        lf_tpd = capacity_tpd * (313.22 / 350.0) # Scaling old baseline ratio
        
        lf_tph = lf_tpd / 24.0
        wte_tph = final_wte_tpd / 24.0
        ad_tph = ad_tpd_total / 24.0
        ptf_tph = plas_tpd / 24.0
        bio_tph = (ad_tpd_total * 0.1078) / 24.0 # Estimate bio composting
        
        lf_mult, wte_mult, ad_mult, ptf_mult, bio_mult = 1.160, 0.510, 0.027, 0.700, 0.300
        
        total_lf = lf_tpd * 365 * lf_mult
        total_wte = final_wte_tpd * 365 * wte_mult
        total_ad = ad_tpd_total * 365 * ad_mult
        total_ptf = plas_tpd * 365 * ptf_mult
        total_bio = (ad_tpd_total * 0.1078) * 365 * bio_mult
        
        total_process = total_wte + total_ad + total_ptf + total_bio
        grand_total_excel = total_lf - total_process

        st.divider()
        st.markdown("<h2 style='text-align: center; color: #2e7d32;'>🌱 Total Plant Carbon Reduction (Excel Logic)</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{grand_total_excel:,.2f} Metric Tons CO2e / Year</h1>", unsafe_allow_html=True)
        st.divider()

        excel_data = {
            "System": ["Landfill Baseline", "WtE Emission", "AD Emission", "PTF Emission", "Bio Composting"],
            "tph": [round(lf_tph, 3), round(wte_tph, 3), round(ad_tph, 3), round(ptf_tph, 3), round(bio_tph, 3)],
            "CO2/ton": [lf_mult, wte_mult, ad_mult, ptf_mult, bio_mult],
            "Days/Annum": [365, 365, 365, 365, 365],
            "CO2/annum (Tons)": [round(total_lf, 2), round(total_wte, 2), round(total_ad, 2), round(total_ptf, 2), round(total_bio, 2)]
        }
        st.dataframe(pd.DataFrame(excel_data), use_container_width=True)
        
    else:
        # --- STANDARD DYNAMIC IPCC MATH ---
        st.markdown("#### 🎛️ Dynamic IPCC Engineering Variables")
        col_env1, col_env2, col_env3, col_env4 = st.columns(4)
        with col_env1:
            st.markdown("**General Framework**")
            ef_grid = st.number_input("Grid Emission Factor", value=0.67, step=0.01)
            gwp_ch4 = st.number_input("Methane GWP", value=28)
            
        with col_env2:
            st.markdown("**AD Plant Metrics**")
            ad_elec_yield = st.number_input("AD Yield (MWh/ton)", value=0.22, format="%.3f")
            ad_parasitic = st.slider("AD Parasitic Load (%)", 0.0, 1.0, 0.10, 0.01)
            
        with col_env3:
            st.markdown("**Pyrolysis Metrics**")
            pyro_elec_yield = st.number_input("Pyro CHP (MWh/ton)", value=0.80, format="%.2f")
            pyro_parasitic = st.slider("Pyro Parasitic (%)", 0.0, 1.0, 0.15, 0.01)
            
        with col_env4:
            st.markdown("**WtE Incinerator Metrics**")
            wte_elec_yield = st.number_input("WtE Yield (MWh/ton)", value=0.37, format="%.2f")
            wte_fossil_ef = st.number_input("Fossil Stack EF", value=0.35, format="%.2f")

        # Simplified math for visualization
        M_wte = final_wte_tpd * 330
        e_offset_wte = (M_wte * wte_elec_yield) * ef_grid
        e_stack_fossil = M_wte * wte_fossil_ef
        total_wte_co2 = e_offset_wte - e_stack_fossil

        M_pyro = plas_tpd * 330
        total_pyro_co2 = (M_pyro * pyro_elec_yield) * ef_grid

        M_ad = ad_tpd_total * 330
        total_ad_co2 = (M_ad * ad_elec_yield) * ef_grid

        grand_total_co2 = total_ad_co2 + total_pyro_co2 + total_wte_co2
        
        st.divider()
        st.markdown("<h2 style='text-align: center; color: #2e7d32;'>🌱 Dynamic Carbon Credits (Grid Offset)</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{grand_total_co2:,.0f} Metric Tons CO2e / Year</h1>", unsafe_allow_html=True)
