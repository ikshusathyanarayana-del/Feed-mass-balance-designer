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
# UI: SIDEBAR INPUTS
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
    cv_pampers = st.number_input("Pampers CV", value=1840, step=100)
    cv_rubber = st.number_input("Rubber CV", value=2400, step=100)
    cv_others = st.number_input("Others CV", value=3200, step=100)
    cv_inerts = 0
    cv_ferrous = 0
    cv_non_ferrous = 0
    cv_org_wet = st.number_input("Organic - WET", value=526, step=10)
    cv_org_dry = st.number_input("Organic - DRY", value=2629, step=10)
    cv_food = st.number_input("Organic - Base (Standard)", value=1200, step=100)

# ==========================================
# DATA COMPILATION
# ==========================================
materials = {
    'Food_Waste': {'pct': food_waste, 'dry_frac': dry_food, 'cv': cv_food},
    'Garden_Waste': {'pct': garden_waste, 'dry_frac': dry_garden, 'cv': cv_food}, 
    'Plastics': {'pct': plastics, 'dry_frac': dry_plastics, 'cv': cv_plastics},
    'Paper_Cardboard': {'pct': paper, 'dry_frac': dry_paper, 'cv': cv_paper},
    'Textile': {'pct': textile, 'dry_frac': dry_textile, 'cv': cv_textile},
    'Pampers': {'pct': pampers, 'dry_frac': dry_pampers, 'cv': cv_pampers},
    'Wood': {'pct': wood, 'dry_frac': dry_wood, 'cv': cv_wood},
    'Inerts': {'pct': inerts, 'dry_frac': dry_inerts, 'cv': cv_inerts},
    'Ferrous': {'pct': ferrous, 'dry_frac': dry_ferrous, 'cv': cv_ferrous},
    'Non_Ferrous': {'pct': non_ferrous, 'dry_frac': dry_non_ferrous, 'cv': cv_non_ferrous},
    'Others': {'pct': others, 'dry_frac': dry_others, 'cv': cv_others},
    'Rubber': {'pct': rubber, 'dry_frac': dry_rubber, 'cv': cv_rubber}
}

total_input_pct = sum(m['pct'] for m in materials.values())

# ==========================================
# CORE ENGINEERING LOGIC
# ==========================================
def run_mass_balance():
    DAYS_PER_YEAR = 330
    HOURS_PER_DAY = 10.0
    ad_tpd_total = 0 # Variable to track mass going to AD

    stream = {}
    for name, props in materials.items():
        tpd = (props['pct'] / 100.0) * capacity_tpd
        dry_tpd = tpd * props['dry_frac']
        stream[name] = {'tpd': tpd, 'dry_tpd': dry_tpd, 'cv': props['cv']}

    dot = graphviz.Digraph(comment='Clean Hybrid Mass Balance', format='png')
    dot.attr(rankdir='TB', nodesep='0.6', ranksep='0.8')
    dot.attr('node', shape='none', fontname='Helvetica', fontsize='9')
    mass_balance_data = []

    def make_mb_node(node_id, title, bgcolor, tpd, dry_tpd, capacity_ref=capacity_tpd):
        if tpd <= 0.01: return None
        pct_total = (tpd / capacity_ref) * 100.0
        tpy = tpd * DAYS_PER_YEAR
        dry_pct = (dry_tpd / tpd) * 100.0 if tpd > 0 else 0
        wet_pct = 100.0 - dry_pct
        
        mass_balance_data.append({
            "Process Node": title, "Tons/Day": round(tpd, 2), "Tons/Year": round(tpy, 0),
            "% Dry": f"{dry_pct:.2f}%", "% Wet": f"{wet_pct:.2f}%"
        })
        
        html = f"""<
        <TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
            <TR><TD COLSPAN="4" BGCOLOR="{bgcolor}"><B>{title}</B></TD></TR>
            <TR><TD>{pct_total:.2f}%</TD><TD>{tpy:,.0f} Tons/Year</TD><TD>Dry Material:</TD><TD>Wet :</TD></TR>
            <TR><TD>330 Days/Year</TD><TD>{tpd:,.2f} Tons/Day</TD><TD>{dry_pct:.2f}%</TD><TD>{wet_pct:.2f}%</TD></TR>
        </TABLE>>"""
        dot.node(node_id, html)
        return tpd

    def make_process_node(node_id, label, color, shape='box'):
        dot.node(node_id, label, shape=shape, style='filled', fillcolor=color, fontname='Helvetica', fontsize='10')

    def current_stream_totals():
        return sum(s['tpd'] for s in stream.values()), sum(s['dry_tpd'] for s in stream.values())

    curr_tpd, curr_dry = current_stream_totals()
    make_mb_node('Reception', 'RECEPTION OF MATERIAL', '#c5e0b4', curr_tpd, curr_dry)
    spine = 'Reception'

    if stream['Ferrous']['tpd'] > 0:
        make_mb_node('MagSep', 'MAGNETIC SEPARATOR', '#ccc1da', curr_tpd, curr_dry)
        dot.edge(spine, 'MagSep', color='#4f81bd', penwidth='3')
        spine = 'MagSep'
        rec_fe = stream['Ferrous']['tpd'] * (eff_mag / 100.0)
        rec_fe_dry = stream['Ferrous']['dry_tpd'] * (eff_mag / 100.0)
        if rec_fe > 0:
            make_mb_node('Ferrous', 'FERROUS MATERIAL', '#f8cbad', rec_fe, rec_fe_dry)
            dot.edge(spine, 'Ferrous', color='#4f81bd', penwidth='2')
            stream['Ferrous']['tpd'] -= rec_fe
            stream['Ferrous']['dry_tpd'] -= rec_fe_dry
        curr_tpd, curr_dry = current_stream_totals()

    if stream['Non_Ferrous']['tpd'] > 0:
        make_mb_node('Eddy', 'EDDY CURRENT SEPARATOR', '#ccc1da', curr_tpd, curr_dry)
        dot.edge(spine, 'Eddy', color='#4f81bd', penwidth='3')
        spine = 'Eddy'
        rec_nf = stream['Non_Ferrous']['tpd'] * (eff_manual / 100.0)
        rec_nf_dry = stream['Non_Ferrous']['dry_tpd'] * (eff_manual / 100.0)
        if rec_nf > 0:
            make_mb_node('NonFerrous', 'NON-FERROUS MATERIAL', '#f8cbad', rec_nf, rec_nf_dry)
            dot.edge(spine, 'NonFerrous', color='#4f81bd', penwidth='2')
            stream['Non_Ferrous']['tpd'] -= rec_nf
            stream['Non_Ferrous']['dry_tpd'] -= rec_nf_dry
        curr_tpd, curr_dry = current_stream_totals()

    org_tpd = stream['Food_Waste']['tpd'] + stream['Garden_Waste']['tpd']
    if org_tpd > 0 and 'AD' in pref_tech:
        make_mb_node('Trommel', 'SPLITTER / SCREW SCREEN', '#e2efda', curr_tpd, curr_dry)
        dot.edge(spine, 'Trommel', color='#4f81bd', penwidth='3')
        spine = 'Trommel'
        
        rec_org_tpd = org_tpd * (eff_trommel / 100.0)
        rec_org_dry = (stream['Food_Waste']['dry_tpd'] + stream['Garden_Waste']['dry_tpd']) * (eff_trommel / 100.0)
        ad_tpd_total = rec_org_tpd # Save AD throughput for emissions math
        
        make_mb_node('Organics', 'ORGANICS TO AD', '#f8cbad', rec_org_tpd, rec_org_dry)
        dot.edge(spine, 'Organics', color='#4f81bd', penwidth='2')
        make_process_node('AD_Plant', 'Anaerobic Digester', '#98FB98')
        dot.edge('Organics', 'AD_Plant', penwidth='2')
        
        for key in ['Food_Waste', 'Garden_Waste']:
            stream[key]['tpd'] *= (1 - (eff_trommel / 100.0))
            stream[key]['dry_tpd'] *= (1 - (eff_trommel / 100.0))
        curr_tpd, curr_dry = current_stream_totals()

    if stream['Inerts']['tpd'] > 0:
        make_mb_node('ManualSort', 'MANUAL SORTING STATION', '#fce4d6', curr_tpd, curr_dry)
        dot.edge(spine, 'ManualSort', color='#4f81bd', penwidth='3')
        spine = 'ManualSort'
        rec_inerts = stream['Inerts']['tpd'] * (eff_manual / 100.0)
        rec_inerts_dry = stream['Inerts']['dry_tpd'] * (eff_manual / 100.0)
        make_mb_node('Inerts', 'INERTS (STONES/GLASS)', '#f8cbad', rec_inerts, rec_inerts_dry)
        dot.edge(spine, 'Inerts', color='#4f81bd', penwidth='2')
        stream['Inerts']['tpd'] -= rec_inerts
        stream['Inerts']['dry_tpd'] -= rec_inerts_dry
        curr_tpd, curr_dry = current_stream_totals()

    if stream['Plastics']['tpd'] > 0 and 'Pyrolysis' in pref_tech:
        make_mb_node('NIR', 'NIR (OPTICAL SORTING)', '#fff2cc', curr_tpd, curr_dry)
        dot.edge(spine, 'NIR', color='#4f81bd', penwidth='3')
        spine = 'NIR'
        rec_plas = stream['Plastics']['tpd'] * (eff_nir / 100.0)
        rec_plas_dry = stream['Plastics']['dry_tpd'] * (eff_nir / 100.0)
        make_mb_node('Plastics', 'PLASTICS TO PYRO', '#f8cbad', rec_plas, rec_plas_dry)
        dot.edge(spine, 'Plastics', color='#4f81bd', penwidth='2')
        make_process_node('Pyro_Reactor', 'Pyrolysis Reactor', '#DDA0DD')
        dot.edge('Plastics', 'Pyro_Reactor', penwidth='2')
        stream['Plastics']['tpd'] -= rec_plas
        stream['Plastics']['dry_tpd'] -= rec_plas_dry
        curr_tpd, curr_dry = current_stream_totals()

    wte_energy_data = []
    total_kcal = 0

    if curr_tpd > 0.01 and 'WtE' in pref_tech:
        make_mb_node('WtE', 'WtE PLANT (RESIDUALS)', '#a9d18e', curr_tpd, curr_dry)
        dot.edge(spine, 'WtE', color='#4f81bd', penwidth='4')
        make_process_node('FGT', 'Flue Gas Treatment', '#D3D3D3')
        dot.edge('WtE', 'FGT', label='Flue Gas', color='red')
        
        for name, data in stream.items():
            tpd_to_wte = data['tpd']
            if tpd_to_wte > 0.01:
                if excel_mode and name in ['Food_Waste', 'Garden_Waste']:
                    leachate_drain = tpd_to_wte * 0.15 
                    adjusted_tpd = tpd_to_wte - leachate_drain
                    half_tpd = adjusted_tpd / 2.0
                    total_kcal += half_tpd * cv_org_wet
                    wte_energy_data.append({"Material": f"{name} (WET)", "Tons/Day": round(half_tpd, 2), "CV (Kcal/kg)": cv_org_wet})
                    total_kcal += half_tpd * cv_org_dry
                    wte_energy_data.append({"Material": f"{name} (DRY)", "Tons/Day": round(half_tpd, 2), "CV (Kcal/kg)": cv_org_dry})
                    continue 

                component_kcal = tpd_to_wte * data['cv']
                total_kcal += component_kcal
                wte_energy_data.append({
                    "Material": name.replace('_', ' '),
                    "Tons/Day": round(tpd_to_wte, 2),
                    "CV (Kcal/kg)": data['cv']
                })
                
    avg_cv_kcal = (total_kcal / curr_tpd) if curr_tpd > 0 else 0
    avg_cv_mj = avg_cv_kcal * 0.004184

    return dot, mass_balance_data, wte_energy_data, avg_cv_kcal, avg_cv_mj, curr_tpd, ad_tpd_total

# Execute core logic
diagram, mb_data, wte_data, avg_cv_kcal, avg_cv_mj, final_wte_tpd, ad_tpd_total = run_mass_balance()

if total_input_pct > 100.1 or total_input_pct < 99.9:
    st.warning(f"⚠️ **Note:** Your composition adds up to {total_input_pct:.2f}%. Ideally it should equal exactly 100%.")

# ==========================================
# UI: TABS LAYOUT
# ==========================================
tab1, tab2 = st.tabs(["📊 Mass Balance & Process Flow", "🌍 Environmental & CO2e Impact"])

with tab1:
    st.subheader("Process Flow & Dynamic Mass Balance")
    st.graphviz_chart(diagram, use_container_width=True)

    st.divider()

    st.subheader("🔥 WtE Energy & Calorific Value Analysis")
    if excel_mode:
        st.info("🧮 **Excel Mode is ON:** The calculations below override standard physical math to match the target Excel file.")

    colA, colB, colC = st.columns(3)
    colA.metric("Total Waste to WtE", f"{final_wte_tpd:.2f} TPD")
    colB.metric("Average CV (Kcal/kg)", f"{avg_cv_kcal:,.0f} Kcal/kg")
    colC.metric("Average CV (MJ/kg)", f"{avg_cv_mj:.2f} MJ/kg")

    col_table1, col_table2 = st.columns(2)
    with col_table1:
        st.markdown("**WtE Residual Makeup**")
        st.dataframe(pd.DataFrame(wte_data), use_container_width=True)
    with col_table2:
        st.markdown("**Overall Mass Balance Data**")
        df_mb = pd.DataFrame(mb_data)
        st.dataframe(df_mb, use_container_width=True)
        csv = df_mb.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Mass Balance CSV", data=csv, file_name="mass_balance.csv", mime="text/csv")


with tab2:
    st.subheader("Anaerobic Digester (AD) CO2e Reduction Model")
    st.markdown("Calculate the exact Greenhouse Gas (GHG) offset generated by the AD plant using IPCC Tier 1 mass balance methodologies.")
    
    # Custom Assumption Sliders
    st.markdown("#### 🎛️ Engineering Assumptions & Variables")
    col_env1, col_env2, col_env3 = st.columns(3)
    with col_env1:
        st.markdown("**IPCC Organic Factors**")
        doc_food = st.number_input("DOC (Food Waste)", value=0.15, step=0.01)
        doc_garden = st.number_input("DOC (Garden Waste)", value=0.20, step=0.01)
        doc_f = st.slider("Fraction Degraded (DOCf)", 0.0, 1.0, 0.50, 0.01)
    with col_env2:
        st.markdown("**Landfill & Climate Metrics**")
        mcf = st.slider("Methane Correction Factor (MCF)", 0.0, 1.0, 1.0, 0.1)
        f_ch4 = st.slider("Landfill Gas CH4 Fraction (F)", 0.0, 1.0, 0.50, 0.01)
        gwp_ch4 = st.number_input("Methane GWP (100-yr)", value=28)
        ef_grid = st.number_input("Grid Emission Factor (tCO2/MWh)", value=0.67, step=0.01)
    with col_env3:
        st.markdown("**AD Biogas & Engine Efficiency**")
        y_biogas = st.number_input("Biogas Yield (m3/ton)", value=100)
        pct_ch4_biogas = st.slider("Biogas CH4 %", 0.0, 1.0, 0.60, 0.01)
        lhv_ch4 = st.number_input("Methane LHV (MWh/m3)", value=0.010, format="%.3f")
        eta_elec = st.slider("CHP Electrical Efficiency", 0.0, 1.0, 0.38, 0.01)
        parasitic_load = st.slider("Plant Parasitic Load (%)", 0.0, 1.0, 0.10, 0.01)

    # --- AD CO2e MATH ENGINE ---
    if 'AD' in pref_tech and ad_tpd_total > 0:
        # 1. Establish Ratios
        total_org_pct = food_waste + garden_waste
        ratio_food = food_waste / total_org_pct if total_org_pct > 0 else 0
        ratio_garden = garden_waste / total_org_pct if total_org_pct > 0 else 0
        
        doc_avg = (ratio_food * doc_food) + (ratio_garden * doc_garden)
        M_ad = ad_tpd_total * 330 # Annual mass to AD
        
        # 2. Methane Avoidance (E_avoid)
        e_avoid = M_ad * doc_avg * doc_f * mcf * f_ch4 * (16/12) * gwp_ch4
        
        # 3. Energy Offset (E_offset)
        e_offset = (M_ad * y_biogas * pct_ch4_biogas * lhv_ch4 * eta_elec) * ef_grid
        
        # 4. Plant Emissions (E_plant)
        e_plant = e_offset * parasitic_load
        
        total_ad_co2_saved = e_avoid + e_offset - e_plant

        # Output Display
        st.divider()
        st.markdown(f"### 📉 Total AD Carbon Reduction: **{total_ad_co2_saved:,.0f} tons of CO2e / year**")
        
        res1, res2, res3 = st.columns(3)
        res1.metric("1. Avoided Methane", f"+ {e_avoid:,.0f} tCO2e", help="Emissions prevented from rotting in a landfill.")
        res2.metric("2. Fossil Grid Offset", f"+ {e_offset:,.0f} tCO2e", help="Emissions saved by generating renewable power.")
        res3.metric("3. Plant Parasitic Load", f"- {e_plant:,.0f} tCO2e", help="Emissions subtracted to power the AD plant itself.")
        
    else:
        st.warning("⚠️ **Anaerobic Digester is either turned off in Client Preferences or the Trommel efficiency is set to 0. Adjust settings to view AD carbon offsets.**")
