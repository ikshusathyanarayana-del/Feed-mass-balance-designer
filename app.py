import streamlit as st
import graphviz
import pandas as pd
import os

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Universal WtE Plant Builder", layout="wide")
st.title("⚙️ Universal Modular Waste-to-Energy Plant Builder")
st.markdown("Dynamically configure any plant architecture. The thermodynamic engine automatically routes mass, calculates Dry/Wet fractions, and outputs the final energy balance.")

# ==========================================
# UI: UNIVERSAL PLANT CONFIGURATOR
# ==========================================
st.sidebar.header("1. Plant Capacity & Baseline")
capacity_tpd = st.sidebar.number_input("Total Plant Intake (TPD)", min_value=10, max_value=10000, value=300, step=10)

st.sidebar.header("2. Build Your Architecture")
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
        'Screw Press (Wet/Dry Split)',
        'Manual Sorting (Inerts)',
        'NIR Optical (Plastics)'
    ]
)

active_destinations = st.sidebar.multiselect(
    "Downstream Energy / Disposal",
    options=['Anaerobic Digestion (AD)', 'Pyrolysis', 'WtE Incinerator', 'Sanitary Landfill'],
    default=['Anaerobic Digestion (AD)', 'Pyrolysis', 'WtE Incinerator']
)

# --- EXPANDER 3: COMPOSITION ---
with st.sidebar.expander("📊 3. Municipal Waste Composition (%)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        food_waste = st.number_input("Food/Organic", value=20.13, step=0.1)
        plastics = st.number_input("Plastics", value=19.69, step=0.1)
        paper = st.number_input("Paper & Cardboard", value=10.0, step=0.1)
        textile = st.number_input("Textiles", value=5.0, step=0.1)
    with col2:
        inerts_nf = st.number_input("Inerts (Glass/Stone)", value=1.72, step=0.1)
        ferrous = st.number_input("Ferrous Metals", value=1.10, step=0.1)
        non_ferrous = st.number_input("Non-Ferrous Metals", value=1.0, step=0.1)
        others_residual = st.number_input("Other Residuals", value=41.36, step=0.1)

# --- EXPANDER 4: MACHINE EFFICIENCIES ---
with st.sidebar.expander("⚙️ 4. Machine Efficiencies (%)", expanded=False):
    eff_bag_leachate = st.slider("Leachate Moisture Drain (%)", 0, 30, 15) if 'Bag Opener (Leachate Drain)' in active_modules else 0
    eff_mag = st.slider("Magnetic Sep (Ferrous Extraction)", 0, 100, 100) if 'Magnetic Separator (Ferrous)' in active_modules else 0
    eff_eddy = st.slider("Eddy Current (Non-Ferrous Ext.)", 0, 100, 100) if 'Eddy Current (Non-Ferrous)' in active_modules else 0
    eff_trommel = st.slider("Trommel (Organics Extraction)", 0, 100, 80) if 'Trommel Screen (Organics)' in active_modules else 0
    screw_press_solid = st.slider("Screw Press (Solid Fraction % to WtE)", 0, 100, 40) if 'Screw Press (Wet/Dry Split)' in active_modules else 0
    eff_manual = st.slider("Manual Sorting (Inerts Ext.)", 0, 100, 100) if 'Manual Sorting (Inerts)' in active_modules else 0
    eff_nir = st.slider("NIR Sorter (Plastics Extraction)", 0, 100, 100) if 'NIR Optical (Plastics)' in active_modules else 0

# --- EXPANDER 5: MOISTURE DATA ---
with st.sidebar.expander("💧 5. Moisture Content (% Dry)", expanded=False):
    st.markdown("*Percentage of solid matter (100% = completely dry)*")
    dry_food = st.number_input("Food Dry %", value=20.0) / 100.0
    dry_plastics = st.number_input("Plastics Dry %", value=100.0) / 100.0
    dry_paper = st.number_input("Paper Dry %", value=80.0) / 100.0
    dry_textile = st.number_input("Textiles Dry %", value=50.0) / 100.0
    dry_inerts = st.number_input("Inerts Dry %", value=100.0) / 100.0
    dry_ferrous = st.number_input("Ferrous Dry %", value=100.0) / 100.0
    dry_non_ferrous = st.number_input("Non-Ferrous Dry %", value=100.0) / 100.0
    dry_others = st.number_input("Other Residuals Dry %", value=80.0) / 100.0

# --- EXPANDER 6: CV DATA ---
with st.sidebar.expander("🔥 6. Calorific Values (Kcal/kg)", expanded=False):
    cv_plastics = st.number_input("Plastics CV", value=3300, step=100)
    cv_org_dry = st.number_input("Dry Organics CV", value=2629, step=10)
    cv_residual = st.number_input("General Residual CV", value=3585, step=100)

# ==========================================
# UNIVERSAL MASS BALANCE ENGINE (W/ DRY TRACKING)
# ==========================================
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

    def make_mb_node(node_id, title, bgcolor, tpd, dry_tpd):
        if tpd < 0.01: return 0
        pct_total = (tpd / capacity_tpd) * 100.0
        tpy = tpd * DAYS_PER_YEAR
        dry_pct = (dry_tpd / tpd) * 100.0 if tpd > 0 else 0
        wet_pct = 100.0 - dry_pct
        
        mass_balance_data.append({"Process Node": title, "Tons/Day": round(tpd, 2), "Tons/Year": round(tpy, 0), "% Dry": f"{dry_pct:.2f}%", "% Wet": f"{wet_pct:.2f}%"})
        
        html = f"""<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
            <TR><TD COLSPAN="4" BGCOLOR="{bgcolor}"><B>{title}</B></TD></TR>
            <TR><TD>{pct_total:.2f}%</TD><TD>{tpy:,.0f} Tons/Year</TD><TD>Dry Material:</TD><TD>Wet :</TD></TR>
            <TR><TD>330 Days/Year</TD><TD>{tpd:,.2f} Tons/Day</TD><TD>{dry_pct:.2f}%</TD><TD>{wet_pct:.2f}%</TD></TR></TABLE>>"""
        dot.node(node_id, html)
        return tpd

    def make_process_node(node_id, label, color, shape='box'):
        dot.node(node_id, label, shape=shape, style='filled', fillcolor=color, fontname='Helvetica', fontsize='10')

    # Initial Dry Mass Calculation
    initial_dry_tpd = capacity_tpd * (
        f_w * dry_food +
        p_w * dry_plastics +
        (paper/total_comp) * dry_paper +
        (textile/total_comp) * dry_textile +
        i_w * dry_inerts +
        fe_w * dry_ferrous +
        nf_w * dry_non_ferrous +
        (others_residual/total_comp) * dry_others
    )

    curr_tpd = capacity_tpd
    curr_dry_tpd = initial_dry_tpd
    
    make_mb_node('Reception', '1. RECEPTION OF MATERIAL', '#c5e0b4', curr_tpd, curr_dry_tpd)
    spine = 'Reception'

    extracted_ad = 0
    extracted_dry_org = 0
    extracted_plas = 0
    rdf_org_tpd = 0
    rdf_org_dry = 0

    # ---------------------------------------------------------
    # DYNAMIC PIPELINE ROUTING
    # ---------------------------------------------------------
    if 'Bag Opener (Leachate Drain)' in active_modules:
        make_mb_node('BagOpener', 'BAG OPENER & DRAIN', '#e2efda', curr_tpd, curr_dry_tpd)
        dot.edge(spine, 'BagOpener', color='#4f81bd', penwidth='3')
        spine = 'BagOpener'
        leachate_tpd = capacity_tpd * (eff_bag_leachate / 100.0)
        leachate_dry = 0 # Leachate is water
        if leachate_tpd > 0:
            make_mb_node('Leachate', 'WASTEWATER / LEACHATE', '#9bc2e6', leachate_tpd, leachate_dry)
            dot.edge(spine, 'Leachate', color='#4f81bd', penwidth='2')
            curr_tpd -= leachate_tpd
            curr_dry_tpd -= leachate_dry

    if 'Magnetic Separator (Ferrous)' in active_modules:
        make_mb_node('MagSep', 'MAGNETIC SEPARATOR', '#ccc1da', curr_tpd, curr_dry_tpd)
        dot.edge(spine, 'MagSep', color='#4f81bd', penwidth='3')
        spine = 'MagSep'
        ferrous_tpd = (capacity_tpd * fe_w) * (eff_mag / 100.0)
        ferrous_dry = ferrous_tpd * dry_ferrous
        if ferrous_tpd > 0:
            make_mb_node('Ferrous', 'RECOVERED FERROUS', '#f8cbad', ferrous_tpd, ferrous_dry)
            dot.edge(spine, 'Ferrous', color='#4f81bd', penwidth='2')
            curr_tpd -= ferrous_tpd
            curr_dry_tpd -= ferrous_dry

    if 'Eddy Current (Non-Ferrous)' in active_modules:
        make_mb_node('Eddy', 'EDDY CURRENT SEPARATOR', '#ccc1da', curr_tpd, curr_dry_tpd)
        dot.edge(spine, 'Eddy', color='#4f81bd', penwidth='3')
        spine = 'Eddy'
        nf_tpd = (capacity_tpd * nf_w) * (eff_eddy / 100.0)
        nf_dry = nf_tpd * dry_non_ferrous
        if nf_tpd > 0:
            make_mb_node('NonFerrous', 'RECOVERED NON-FERROUS', '#f8cbad', nf_tpd, nf_dry)
            dot.edge(spine, 'NonFerrous', color='#4f81bd', penwidth='2')
            curr_tpd -= nf_tpd
            curr_dry_tpd -= nf_dry

    if 'Trommel Screen (Organics)' in active_modules:
        make_mb_node('Trommel', 'TROMMEL SCREEN', '#e2efda', curr_tpd, curr_dry_tpd)
        dot.edge(spine, 'Trommel', color='#4f81bd', penwidth='3')
        spine = 'Trommel'
        org_extracted = (capacity_tpd * f_w) * (eff_trommel / 100.0)
        org_dry_total = org_extracted * dry_food
        
        if org_extracted > 0:
            curr_tpd -= org_extracted
            curr_dry_tpd -= org_dry_total
            if 'Screw Press (Wet/Dry Split)' in active_modules:
                make_mb_node('ScrewPress', 'ORGANICS SCREW PRESS', '#ffe699', org_extracted, org_dry_total)
                dot.edge(spine, 'ScrewPress', color='#4f81bd', penwidth='2')
                
                rdf_org_tpd = org_extracted * (screw_press_solid / 100.0)
                rdf_org_dry = min(org_dry_total, rdf_org_tpd) # Assume screw press extracts mostly dry mass
                ltp_org_tpd = org_extracted - rdf_org_tpd
                ltp_org_dry = org_dry_total - rdf_org_dry
                
                extracted_ad = ltp_org_tpd
                extracted_dry_org = rdf_org_tpd
                
                make_mb_node('WetOrg', 'WET ORGANICS (LIQUID)', '#9bc2e6', ltp_org_tpd, ltp_org_dry)
                dot.edge('ScrewPress', 'WetOrg', color='blue', penwidth='1')
                make_mb_node('DryOrg', 'DRY MATERIAL TO RDF', '#f8cbad', rdf_org_tpd, rdf_org_dry)
                dot.edge('ScrewPress', 'DryOrg', color='orange', penwidth='1')
            else:
                extracted_ad = org_extracted
                make_mb_node('WetOrg', 'EXTRACTED ORGANICS', '#f8cbad', org_extracted, org_dry_total)
                dot.edge(spine, 'WetOrg', color='#4f81bd', penwidth='2')

    if 'Manual Sorting (Inerts)' in active_modules:
        make_mb_node('ManualSort', 'MANUAL SORTING', '#fce4d6', curr_tpd, curr_dry_tpd)
        dot.edge(spine, 'ManualSort', color='#4f81bd', penwidth='3')
        spine = 'ManualSort'
        inerts_tpd = (capacity_tpd * i_w) * (eff_manual / 100.0)
        inerts_dry = inerts_tpd * dry_inerts
        if inerts_tpd > 0:
            make_mb_node('Inerts', 'REJECTS / INERTS', '#f8cbad', inerts_tpd, inerts_dry)
            dot.edge(spine, 'Inerts', color='#4f81bd', penwidth='2')
            curr_tpd -= inerts_tpd
            curr_dry_tpd -= inerts_dry

    if 'NIR Optical (Plastics)' in active_modules:
        make_mb_node('NIR', 'NIR OPTICAL SORTER', '#fff2cc', curr_tpd, curr_dry_tpd)
        dot.edge(spine, 'NIR', color='#4f81bd', penwidth='3')
        spine = 'NIR'
        extracted_plas = (capacity_tpd * p_w) * (eff_nir / 100.0)
        plas_dry = extracted_plas * dry_plastics
        if extracted_plas > 0:
            make_mb_node('Plastics', 'RECOVERED PLASTICS', '#f8cbad', extracted_plas, plas_dry)
            dot.edge(spine, 'Plastics', color='#4f81bd', penwidth='2')
            curr_tpd -= extracted_plas
            curr_dry_tpd -= plas_dry

    # ---------------------------------------------------------
    # DOWNSTREAM DESTINATION ROUTING
    # ---------------------------------------------------------
    final_residual_tpd = curr_tpd
    final_residual_dry = curr_dry_tpd

    if 'Anaerobic Digestion (AD)' in active_destinations and extracted_ad > 0:
        make_process_node('AD_Plant', 'Anaerobic Digester\n(Biogas Plant)', '#98FB98')
        dot.edge('WetOrg', 'AD_Plant', penwidth='2')
    elif extracted_ad > 0:
        make_process_node('Compost', 'Composting / Landfill', '#D3D3D3')
        dot.edge('WetOrg', 'Compost', style='dashed')

    if 'Pyrolysis' in active_destinations and extracted_plas > 0:
        make_process_node('Pyro_Plant', 'Pyrolysis Reactor\n(Synthetic Fuel)', '#DDA0DD')
        dot.edge('Plastics', 'Pyro_Plant', penwidth='2')
    elif extracted_plas > 0:
        make_process_node('Baler', 'Plastic Baling for Sale', '#D3D3D3')
        dot.edge('Plastics', 'Baler', style='dashed')

    final_wte_feed = 0
    total_kcal = 0
    wte_energy_data = []

    if 'WtE Incinerator' in active_destinations:
        final_wte_feed = final_residual_tpd + rdf_org_tpd
        final_wte_dry = final_residual_dry + rdf_org_dry
        
        make_mb_node('WtE', 'WtE INCINERATOR', '#a9d18e', final_wte_feed, final_wte_dry)
        dot.edge(spine, 'WtE', label='General Residuals', color='#4f81bd', penwidth='4')
        if rdf_org_tpd > 0:
            dot.edge('DryOrg', 'WtE', label='Dry Organics', color='orange', style='dashed', penwidth='2')
        
        make_process_node('Turbine', 'Steam Turbine', '#FFD700')
        dot.edge('WtE', 'Turbine', color='blue')

        wte_energy_data.append({"Material": "General Residuals", "Tons/Day": round(final_residual_tpd, 2), "CV (Kcal/kg)": cv_residual})
        total_kcal += final_residual_tpd * cv_residual
        if rdf_org_tpd > 0:
            wte_energy_data.append({"Material": "Dry Organics", "Tons/Day": round(rdf_org_tpd, 2), "CV (Kcal/kg)": cv_org_dry})
            total_kcal += rdf_org_tpd * cv_org_dry

    elif 'Sanitary Landfill' in active_destinations:
        final_wte_feed = final_residual_tpd + rdf_org_tpd
        final_wte_dry = final_residual_dry + rdf_org_dry
        make_mb_node('Landfill', 'SANITARY LANDFILL', '#A9A9A9', final_wte_feed, final_wte_dry)
        dot.edge(spine, 'Landfill', label='Residual Waste', color='#4f81bd', penwidth='4')
        if rdf_org_tpd > 0:
            dot.edge('DryOrg', 'Landfill', color='orange', style='dashed', penwidth='2')

    avg_cv_kcal = (total_kcal / final_wte_feed) if final_wte_feed > 0 else 0
    avg_cv_mj = avg_cv_kcal * 0.004184

    return dot, mass_balance_data, wte_energy_data, avg_cv_kcal, avg_cv_mj, final_wte_feed, extracted_ad, extracted_plas

diagram, mb_data, wte_data, avg_cv_kcal, avg_cv_mj, final_wte_feed, extracted_ad, extracted_plas = run_universal_mass_balance()

# ==========================================
# UI: DISPLAY DASHBOARD
# ==========================================
tab1, tab2 = st.tabs(["📊 Mass Balance & Thermodynamics", "🌍 Environmental & CO2e Impact"])

with tab1:
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

with tab2:
    st.subheader("🌍 Environmental & CO2e Reduction Models")
    
    match_excel_co2 = st.toggle("🧮 Match Excel CO2 Logic", value=True, help="Applies flat multipliers from legacy spreadsheets (365 days, 0 grid offsets).")

    if match_excel_co2:
        st.warning("⚠️ **Excel Mode is ON:** Calculating emissions using legacy flat-multiplier formulas (365 days/year, NO grid offsets).")
        
        lf_tpd = capacity_tpd * (313.22 / 350.0)
        
        lf_tph = lf_tpd / 24.0
        wte_tph = final_wte_feed / 24.0
        ad_tph = extracted_ad / 24.0
        ptf_tph = extracted_plas / 24.0
        bio_tph = (extracted_ad * 0.1078) / 24.0 
        
        lf_mult, wte_mult, ad_mult, ptf_mult, bio_mult = 1.160, 0.510, 0.027, 0.700, 0.300
        
        total_lf = lf_tpd * 365 * lf_mult
        total_wte = final_wte_feed * 365 * wte_mult
        total_ad = extracted_ad * 365 * ad_mult
        total_ptf = extracted_plas * 365 * ptf_mult
        total_bio = (extracted_ad * 0.1078) * 365 * bio_mult
        
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

        M_wte = final_wte_feed * 330
        e_offset_wte = (M_wte * wte_elec_yield) * ef_grid
        e_stack_fossil = M_wte * wte_fossil_ef
        total_wte_co2 = e_offset_wte - e_stack_fossil

        M_pyro = extracted_plas * 330
        total_pyro_co2 = (M_pyro * pyro_elec_yield) * ef_grid

        M_ad = extracted_ad * 330
        total_ad_co2 = (M_ad * ad_elec_yield) * ef_grid

        grand_total_co2 = total_ad_co2 + total_pyro_co2 + total_wte_co2
        
        st.divider()
        st.markdown("<h2 style='text-align: center; color: #2e7d32;'>🌱 Dynamic Carbon Credits (Grid Offset)</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{grand_total_co2:,.0f} Metric Tons CO2e / Year</h1>", unsafe_allow_html=True)
