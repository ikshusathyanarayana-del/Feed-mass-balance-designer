import streamlit as st
import graphviz
import pandas as pd
import os

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Dynamic FEED Designer", layout="wide")
st.title("⚙️ Universal Waste-to-Energy Plant Designer")
st.markdown("Universal mass balance routing with downstream process systems, an interactive Calorific Value (CV) toggle, and Environmental Impact modeling.")

# ==========================================
# UI: SIDEBAR INPUTS
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)
else:
    st.sidebar.markdown("*(Upload a 'logo.png' or 'logo.jpg' to GitHub to display your company logo here)*")

st.sidebar.divider()
tutorial_mode = st.sidebar.toggle("🎓 Enable Tutorial / Guide Mode", value=False)
if tutorial_mode:
    st.sidebar.info("💡 **Welcome to Tutorial Mode!** As you scroll through the app, look for these blue boxes. They will explain exactly what each control does and how it impacts the plant's design.")
st.sidebar.divider()

st.sidebar.header("1. Operational Input")
if tutorial_mode:
    st.sidebar.info("💡 **Plant Capacity:** This is the master scale for the whole plant. Changing this recalculates the TPD (Tons Per Day) for every single machine downstream.")
capacity_tpd = st.sidebar.number_input("Plant Capacity (TPD)", min_value=10, max_value=5000, value=350, step=10)

excel_mode = st.sidebar.toggle("🧮 Match Excel CV Logic", value=True)
if tutorial_mode:
    st.sidebar.info("💡 **Excel Override:** When ON, this forces the WtE math to simulate a 15% leachate drain and a 50/50 wet/dry organic split to perfectly match the target baseline engineering spreadsheet.")

st.sidebar.header("2. Build Your Architecture")
if tutorial_mode:
    st.sidebar.info("💡 **Universal Routing:** Add or remove machines here. The mass balance engine will automatically rewire the flowchart and route the garbage accordingly.")

active_modules = st.sidebar.multiselect(
    "Active Sorting Modules",
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

energy_output = st.sidebar.multiselect(
    "Desired Energy Output",
    options=['Electricity', 'Biogas', 'Fuel Oil'],
    default=['Electricity', 'Biogas', 'Fuel Oil']
)

# --- EXPANDER 3: COMPOSITION ---
with st.sidebar.expander("📊 3. Waste Composition (%)", expanded=False):
    if tutorial_mode:
        st.info("💡 **Waste Profile:** Adjust these percentages based on municipal waste studies. Changing the amount of plastics or food waste will completely alter the energy output and carbon footprint of the plant.")
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
    if tutorial_mode:
        st.info("💡 **Equipment Sorting:** No machine is 100% perfect. For example, if you lower the NIR Sorter efficiency to 37%, it proves that some plastic slips past the cameras and ends up burning in the WtE incinerator instead of going to Pyrolysis.")
    eff_bag_leachate = st.slider("Leachate Drain (%)", 0, 30, 15) if 'Bag Opener (Leachate Drain)' in active_modules else 0
    eff_nir = st.slider("NIR Sorter (Plastics)", 0, 100, 37) if 'NIR Optical (Plastics)' in active_modules else 0
    eff_trommel = st.slider("Trommel (Organics)", 0, 100, 62) if 'Trommel Screen (Organics)' in active_modules else 0
    screw_press_solid = st.slider("Screw Press Solid Yield (%)", 0, 100, 40) if 'Screw Press (Wet/Dry Split)' in active_modules else 0
    eff_mag = st.slider("Magnetic Sep (Ferrous)", 0, 100, 100) if 'Magnetic Separator (Ferrous)' in active_modules else 0
    eff_eddy = st.slider("Eddy Current (Non-Ferrous)", 0, 100, 100) if 'Eddy Current (Non-Ferrous)' in active_modules else 0
    eff_manual = st.slider("Manual Sorting (Inerts)", 0, 100, 100) if 'Manual Sorting (Inerts)' in active_modules else 0

# --- EXPANDER 5: MOISTURE & CV DATA ---
with st.sidebar.expander("💧 & 🔥 5. Moisture & CV Data", expanded=False):
    if tutorial_mode:
        st.info("💡 **Thermodynamics:** These numbers dictate how much water is in the garbage and how much heat it produces when burned. These are highly technical values that dictate the final Steam Turbine output.")
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
# DATA COMPILATION & UNIVERSAL MASS BALANCE ENGINE
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

def run_universal_mass_balance():
    DAYS_PER_YEAR = 330
    ad_tpd_total = 0 
    plastic_tpd_to_pyro = 0

    # Build initial active streams
    stream = {}
    for name, props in materials.items():
        tpd = (props['pct'] / 100.0) * capacity_tpd
        dry_tpd = tpd * props['dry_frac']
        stream[name] = {'tpd': tpd, 'dry_tpd': dry_tpd, 'cv': props['cv']}

    dot = graphviz.Digraph(comment='Universal Hybrid Mass Balance', format='png')
    dot.attr(rankdir='TB', nodesep='0.6', ranksep='0.8')
    dot.attr('node', shape='none', fontname='Helvetica', fontsize='9')
    mass_balance_data = []

    def make_mb_node(node_id, title, bgcolor, tpd, dry_tpd, capacity_ref=capacity_tpd):
        if tpd <= 0.01: return None
        pct_total = (tpd / capacity_ref) * 100.0
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

    def current_stream_totals():
        return sum(s['tpd'] for s in stream.values()), sum(s['dry_tpd'] for s in stream.values())

    curr_tpd, curr_dry = current_stream_totals()
    make_mb_node('Reception', 'RECEPTION OF MATERIAL', '#c5e0b4', curr_tpd, curr_dry)
    spine = 'Reception'

    # --- DYNAMIC ROUTING ---
    if 'Bag Opener (Leachate Drain)' in active_modules:
        make_mb_node('BagOpener', 'BAG OPENER & DRAIN', '#e2efda', curr_tpd, curr_dry)
        dot.edge(spine, 'BagOpener', color='#4f81bd', penwidth='3')
        spine = 'BagOpener'
        leachate_tpd = capacity_tpd * (eff_bag_leachate / 100.0)
        # Deduct water proportionally from Food and Garden wet mass to preserve their dry mass
        org_wet = stream['Food_Waste']['tpd'] + stream['Garden_Waste']['tpd']
        if org_wet > 0 and leachate_tpd <= org_wet:
            stream['Food_Waste']['tpd'] -= leachate_tpd * (stream['Food_Waste']['tpd']/org_wet)
            stream['Garden_Waste']['tpd'] -= leachate_tpd * (stream['Garden_Waste']['tpd']/org_wet)
        if leachate_tpd > 0:
            make_mb_node('Leachate', 'WASTEWATER / LEACHATE', '#9bc2e6', leachate_tpd, 0) # 0 dry mass
            dot.edge(spine, 'Leachate', color='#4f81bd', penwidth='2')
        curr_tpd, curr_dry = current_stream_totals()

    if 'Magnetic Separator (Ferrous)' in active_modules and stream['Ferrous']['tpd'] > 0:
        make_mb_node('MagSep', 'MAGNETIC SEPARATOR', '#ccc1da', curr_tpd, curr_dry)
        dot.edge(spine, 'MagSep', color='#4f81bd', penwidth='3')
        spine = 'MagSep'
        rec_fe = stream['Ferrous']['tpd'] * (eff_mag / 100.0)
        rec_fe_dry = stream['Ferrous']['dry_tpd'] * (eff_mag / 100.0)
        if rec_fe > 0:
            make_mb_node('Ferrous', 'RECOVERED FERROUS', '#f8cbad', rec_fe, rec_fe_dry)
            dot.edge(spine, 'Ferrous', color='#4f81bd', penwidth='2')
            stream['Ferrous']['tpd'] -= rec_fe
            stream['Ferrous']['dry_tpd'] -= rec_fe_dry
        curr_tpd, curr_dry = current_stream_totals()

    if 'Eddy Current (Non-Ferrous)' in active_modules and stream['Non_Ferrous']['tpd'] > 0:
        make_mb_node('Eddy', 'EDDY CURRENT SEPARATOR', '#ccc1da', curr_tpd, curr_dry)
        dot.edge(spine, 'Eddy', color='#4f81bd', penwidth='3')
        spine = 'Eddy'
        rec_nf = stream['Non_Ferrous']['tpd'] * (eff_eddy / 100.0)
        rec_nf_dry = stream['Non_Ferrous']['dry_tpd'] * (eff_eddy / 100.0)
        if rec_nf > 0:
            make_mb_node('NonFerrous', 'RECOVERED NON-FERROUS', '#f8cbad', rec_nf, rec_nf_dry)
            dot.edge(spine, 'NonFerrous', color='#4f81bd', penwidth='2')
            stream['Non_Ferrous']['tpd'] -= rec_nf
            stream['Non_Ferrous']['dry_tpd'] -= rec_nf_dry
        curr_tpd, curr_dry = current_stream_totals()

    org_tpd = stream['Food_Waste']['tpd'] + stream['Garden_Waste']['tpd']
    if 'Trommel Screen (Organics)' in active_modules and org_tpd > 0:
        make_mb_node('Trommel', 'TROMMEL SCREEN', '#e2efda', curr_tpd, curr_dry)
        dot.edge(spine, 'Trommel', color='#4f81bd', penwidth='3')
        spine = 'Trommel'
        
        ext_food = stream['Food_Waste']['tpd'] * (eff_trommel / 100.0)
        ext_food_dry = stream['Food_Waste']['dry_tpd'] * (eff_trommel / 100.0)
        ext_garden = stream['Garden_Waste']['tpd'] * (eff_trommel / 100.0)
        ext_garden_dry = stream['Garden_Waste']['dry_tpd'] * (eff_trommel / 100.0)
        
        org_extracted = ext_food + ext_garden
        org_extracted_dry = ext_food_dry + ext_garden_dry
        
        stream['Food_Waste']['tpd'] -= ext_food
        stream['Food_Waste']['dry_tpd'] -= ext_food_dry
        stream['Garden_Waste']['tpd'] -= ext_garden
        stream['Garden_Waste']['dry_tpd'] -= ext_garden_dry
        
        if 'Screw Press (Wet/Dry Split)' in active_modules:
            make_mb_node('ScrewPress', 'ORGANICS SCREW PRESS', '#ffe699', org_extracted, org_extracted_dry)
            dot.edge(spine, 'ScrewPress', color='#4f81bd', penwidth='2')
            
            rdf_org_tpd = org_extracted * (screw_press_solid / 100.0)
            rdf_org_dry = min(org_extracted_dry, rdf_org_tpd)
            ltp_org_tpd = org_extracted - rdf_org_tpd
            ltp_org_dry = org_extracted_dry - rdf_org_dry
            
            ad_tpd_total = ltp_org_tpd
            stream['Screw_Press_Dry'] = {'tpd': rdf_org_tpd, 'dry_tpd': rdf_org_dry, 'cv': cv_org_dry}
            
            make_mb_node('WetOrg', 'WET ORGANICS (LIQUID)', '#9bc2e6', ltp_org_tpd, ltp_org_dry)
            dot.edge('ScrewPress', 'WetOrg', color='blue', penwidth='1')
            make_mb_node('DryOrg', 'DRY MATERIAL TO RDF', '#f8cbad', rdf_org_tpd, rdf_org_dry)
            dot.edge('ScrewPress', 'DryOrg', color='orange', penwidth='1')
            org_node_source = 'WetOrg'
        else:
            ad_tpd_total = org_extracted
            make_mb_node('Organics', 'EXTRACTED ORGANICS', '#f8cbad', org_extracted, org_extracted_dry)
            dot.edge(spine, 'Organics', color='#4f81bd', penwidth='2')
            org_node_source = 'Organics'

        # Route Organics destination
        if 'Anaerobic Digestion (AD)' in active_destinations and ad_tpd_total > 0:
            make_process_node('AD_Plant', 'Anaerobic Digester\n(Biogas Plant)', '#98FB98')
            dot.edge(org_node_source, 'AD_Plant', penwidth='2')
            if 'Biogas' in energy_output or 'Electricity' in energy_output:
                make_process_node('Biogas', 'Biogas Output', '#FFD700', shape='ellipse')
                dot.edge('AD_Plant', 'Biogas', color='orange')
                if 'Electricity' in energy_output:
                    make_process_node('AD_CHP', 'AD CHP Engine', '#FFD700')
                    dot.edge('Biogas', 'AD_CHP', color='orange')
        elif ad_tpd_total > 0:
            make_process_node('Compost', 'Composting / Fertilizer', '#8FBC8F', shape='cylinder')
            dot.edge(org_node_source, 'Compost', style='dashed')
            
        curr_tpd, curr_dry = current_stream_totals()

    if 'Manual Sorting (Inerts)' in active_modules and stream['Inerts']['tpd'] > 0:
        make_mb_node('ManualSort', 'MANUAL SORTING', '#fce4d6', curr_tpd, curr_dry)
        dot.edge(spine, 'ManualSort', color='#4f81bd', penwidth='3')
        spine = 'ManualSort'
        rec_inerts = stream['Inerts']['tpd'] * (eff_manual / 100.0)
        rec_inerts_dry = stream['Inerts']['dry_tpd'] * (eff_manual / 100.0)
        if rec_inerts > 0:
            make_mb_node('Inerts', 'REJECTS / INERTS', '#f8cbad', rec_inerts, rec_inerts_dry)
            dot.edge(spine, 'Inerts', color='#4f81bd', penwidth='2')
            stream['Inerts']['tpd'] -= rec_inerts
            stream['Inerts']['dry_tpd'] -= rec_inerts_dry
        curr_tpd, curr_dry = current_stream_totals()

    if 'NIR Optical (Plastics)' in active_modules and stream['Plastics']['tpd'] > 0:
        make_mb_node('NIR', 'NIR OPTICAL SORTER', '#fff2cc', curr_tpd, curr_dry)
        dot.edge(spine, 'NIR', color='#4f81bd', penwidth='3')
        spine = 'NIR'
        rec_plas = stream['Plastics']['tpd'] * (eff_nir / 100.0)
        rec_plas_dry = stream['Plastics']['dry_tpd'] * (eff_nir / 100.0)
        plastic_tpd_to_pyro = rec_plas
        if rec_plas > 0:
            make_mb_node('Plastics', 'RECOVERED PLASTICS', '#f8cbad', rec_plas, rec_plas_dry)
            dot.edge(spine, 'Plastics', color='#4f81bd', penwidth='2')
            
            # Route Plastics Destination
            if 'Pyrolysis' in active_destinations:
                make_process_node('Pyro_Reactor', 'Pyrolysis Reactor\n& Condenser', '#DDA0DD')
                dot.edge('Plastics', 'Pyro_Reactor', penwidth='2')
                if 'Fuel Oil' in energy_output or 'Electricity' in energy_output:
                    make_process_node('Fuel_Oil', 'Synthetic Fuel Oil', '#FFD700', shape='ellipse')
                    dot.edge('Pyro_Reactor', 'Fuel_Oil', color='orange')
                    if 'Electricity' in energy_output:
                        make_process_node('Pyro_CHP', 'Pyro CHP Engine', '#FFD700')
                        dot.edge('Fuel_Oil', 'Pyro_CHP', color='orange')
            else:
                make_process_node('Baler', 'Plastic Baling for Sale', '#D3D3D3')
                dot.edge('Plastics', 'Baler', style='dashed')
                
            stream['Plastics']['tpd'] -= rec_plas
            stream['Plastics']['dry_tpd'] -= rec_plas_dry
        curr_tpd, curr_dry = current_stream_totals()

    wte_energy_data = []
    total_kcal = 0
    final_wte_feed = 0

    if curr_tpd > 0.01:
        if 'WtE Incinerator' in active_destinations:
            final_wte_feed = curr_tpd
            make_mb_node('WtE', 'WtE PLANT (RESIDUALS)', '#a9d18e', curr_tpd, curr_dry)
            dot.edge(spine, 'WtE', color='#4f81bd', penwidth='4')
            if 'Screw Press (Wet/Dry Split)' in active_modules and 'DryOrg' in [n['Process Node'] for n in mass_balance_data]:
                dot.edge('DryOrg', 'WtE', label='Dry Organics', color='orange', style='dashed', penwidth='2')
            
            make_process_node('FGT', 'Flue Gas Treatment', '#D3D3D3')
            dot.edge('WtE', 'FGT', label='Flue Gas', color='red')
            if 'Electricity' in energy_output:
                make_process_node('Turbine', 'Steam Turbine', '#FFD700')
                dot.edge('WtE', 'Turbine', label='Steam', color='blue')
            
            for name, data in stream.items():
                tpd_to_wte = data['tpd']
                if tpd_to_wte > 0.01:
                    if excel_mode and name in ['Food_Waste', 'Garden_Waste'] and 'Bag Opener (Leachate Drain)' not in active_modules:
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
                    wte_energy_data.append({"Material": name.replace('_', ' '), "Tons/Day": round(tpd_to_wte, 2), "CV (Kcal/kg)": data['cv']})
        
        elif 'Sanitary Landfill' in active_destinations:
            final_wte_feed = curr_tpd
            make_mb_node('Landfill', 'SANITARY LANDFILL', '#A9A9A9', curr_tpd, curr_dry)
            dot.edge(spine, 'Landfill', label='Residual Waste', color='#4f81bd', penwidth='4')
            if 'Screw Press (Wet/Dry Split)' in active_modules and 'DryOrg' in [n['Process Node'] for n in mass_balance_data]:
                dot.edge('DryOrg', 'Landfill', color='orange', style='dashed', penwidth='2')
                
    avg_cv_kcal = (total_kcal / curr_tpd) if curr_tpd > 0 else 0
    avg_cv_mj = avg_cv_kcal * 0.004184

    return dot, mass_balance_data, wte_energy_data, avg_cv_kcal, avg_cv_mj, final_wte_feed, ad_tpd_total, plastic_tpd_to_pyro

diagram, mb_data, wte_data, avg_cv_kcal, avg_cv_mj, final_wte_tpd, ad_tpd_total, plastic_tpd_to_pyro = run_universal_mass_balance()

if total_input_pct > 100.1 or total_input_pct < 99.9:
    st.warning(f"⚠️ **Note:** Your composition adds up to {total_input_pct:.2f}%. Ideally it should equal exactly 100%.")

# ==========================================
# UI: TABS LAYOUT
# ==========================================
tab1, tab2 = st.tabs(["📊 Mass Balance & Process Flow", "🌍 Environmental & CO2e Impact"])

with tab1:
    st.subheader("Process Flow & Dynamic Mass Balance")
    if tutorial_mode:
        st.info("💡 **Graphviz Engine:** This flow diagram generates automatically in real-time. If you change the Plant Capacity to 500 in the sidebar, watch the 'Tons/Day' metrics inside these boxes instantly update.")
    st.graphviz_chart(diagram, use_container_width=True)
    st.divider()
    
    st.subheader("🔥 WtE Energy & Calorific Value Analysis")
    if tutorial_mode:
        st.info("💡 **Calorific Value (CV):** This section proves to the engineers that the final residual garbage entering the incinerator has enough heat energy to sustain a fire and spin the steam turbine without needing auxiliary fuel.")
    
    colA, colB, colC = st.columns(3)
    if 'WtE Incinerator' in active_destinations:
        colA.metric("Total Waste to WtE", f"{final_wte_tpd:.2f} TPD")
        colB.metric("Average CV (Kcal/kg)", f"{avg_cv_kcal:,.0f} Kcal/kg")
        colC.metric("Average CV (MJ/kg)", f"{avg_cv_mj:.2f} MJ/kg")
    else:
        colA.metric("Total Waste to Landfill", f"{final_wte_tpd:.2f} TPD")
        colB.metric("Organics Diverted", f"{ad_tpd_total:.2f} TPD")
        colC.metric("Plastics Diverted", f"{plastic_tpd_to_pyro:.2f} TPD")

    col_table1, col_table2 = st.columns(2)
    with col_table1:
        if len(wte_data) > 0 and 'WtE Incinerator' in active_destinations:
            st.markdown("**WtE Residual Makeup**")
            st.dataframe(pd.DataFrame(wte_data), use_container_width=True)
        else:
            st.info("WtE Incinerator is off. Residuals sent to Landfill.")
    with col_table2:
        st.markdown("**Overall Mass Balance Data**")
        df_mb = pd.DataFrame(mb_data)
        st.dataframe(df_mb, use_container_width=True)

with tab2:
    st.subheader("🌍 Environmental & CO2e Reduction Models")
    if tutorial_mode:
        st.info("💡 **Environmental Models:** This tab runs complex greenhouse gas physics. You can either use dynamic, real-world IPCC physics, or force the app to match a legacy flat-multiplier spreadsheet.")
        
    # --- THE NEW EXCEL MATCH TOGGLE ---
    match_excel_co2 = st.toggle("🧮 Match Excel CO2 Logic", value=True, help="Overrides dynamic IPCC physics. Takes dynamic tonnages from your mass balance and applies the flat multipliers from the client's Excel screenshot (365 days, 0 grid offsets).")

    if match_excel_co2:
        st.warning("⚠️ **Excel Mode is ON:** Using your dynamic mass balance tonnages, but calculating emissions using the flat-multiplier formulas from the legacy spreadsheet (365 days/year, NO grid offsets).")
        
        lf_tpd = capacity_tpd * (313.22 / 350.0) 
        
        # Determine if we need to do the ghost drain or if the module already extracted it
        wte_tpd = final_wte_tpd
        if 'Bag Opener (Leachate Drain)' not in active_modules:
            plant_leachate = capacity_tpd * 0.15
            wte_tpd = max(0, final_wte_tpd - plant_leachate)
            
        ad_tpd = ad_tpd_total
        ptf_tpd = plastic_tpd_to_pyro
        bio_tpd = ad_tpd * (15.744 / 146.048) if ad_tpd > 0 else 0
        
        lf_tph = lf_tpd / 24.0
        wte_tph = wte_tpd / 24.0
        ad_tph = ad_tpd / 24.0
        ptf_tph = ptf_tpd / 24.0
        bio_tph = bio_tpd / 24.0
        
        lf_mult = 1.160
        wte_mult = 0.510
        ad_mult = 0.027
        ptf_mult = 0.700
        bio_mult = 0.300
        
        total_lf = lf_tpd * 365 * lf_mult
        total_wte = wte_tpd * 365 * wte_mult
        total_ad = ad_tpd * 365 * ad_mult
        total_ptf = ptf_tpd * 365 * ptf_mult
        total_bio = bio_tpd * 365 * bio_mult
        
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
            "Hr/day": [24, 24, 24, 24, 24],
            "Days/Annum": [365, 365, 365, 365, 365],
            "CO2/annum (Tons)": [round(total_lf, 2), round(total_wte, 2), round(total_ad, 2), round(total_ptf, 2), round(total_bio, 2)]
        }
        st.dataframe(pd.DataFrame(excel_data), use_container_width=True)
        
    else:
        # --- STANDARD DYNAMIC IPCC MATH ---
        st.markdown("Toggle the subsystems below to instantly calculate your combined Greenhouse Gas (GHG) offsets independent of the main plant layout.")
        t_col1, t_col2, t_col3 = st.columns(3)
        with t_col1: calc_ad = st.toggle("🟢 Include AD Emissions", value=True)
        with t_col2: calc_pyro = st.toggle("🟣 Include Pyrolysis Emissions", value=True)
        with t_col3: calc_wte = st.toggle("🔴 Include WtE Emissions", value=True)

        if tutorial_mode:
            st.info("💡 **Subsystem Toggles:** If you want to see exactly how much carbon *just* the AD plant saves, turn off the Pyrolysis and WtE switches. The Grand Total will instantly recalculate.")

        total_ad_co2 = 0
        total_pyro_co2 = 0
        total_wte_co2 = 0
        st.divider()
        
        st.markdown("#### 🎛️ Engineering Assumptions & Variables")
        col_env1, col_env2, col_env3, col_env4 = st.columns(4)
        with col_env1:
            st.markdown("**General Framework**")
            ef_grid = st.number_input("Grid Emission Factor (tCO2/MWh)", value=0.67, step=0.01)
            gwp_ch4 = st.number_input("Methane GWP (100-yr)", value=28)
            mcf = st.slider("Methane Correction Factor", 0.0, 1.0, 1.0, 0.1)
            f_ch4 = st.slider("Landfill CH4 Fraction", 0.0, 1.0, 0.50, 0.01)
            
        with col_env2:
            st.markdown("**AD Plant Metrics**")
            doc_avg_base = st.slider("Average DOC (Organics)", 0.05, 0.30, 0.16, 0.01)
            doc_f = st.slider("Fraction Degraded (DOCf)", 0.0, 1.0, 0.50, 0.01)
            ad_elec_yield = st.number_input("AD Yield (MWh/ton)", value=0.224, format="%.3f")
            ad_parasitic = st.slider("AD Parasitic Load (%)", 0.0, 1.0, 0.10, 0.01)
            
        with col_env3:
            st.markdown("**Pyrolysis Metrics**")
            pyro_oil_yield = st.number_input("Oil Yield (Liters/ton)", value=450)
            pyro_fuel_offset = st.number_input("Fuel Offset (tCO2/L)", value=0.00268, format="%.5f")
            pyro_elec_yield = st.number_input("Pyro CHP (MWh/ton)", value=1.92, format="%.2f")
            pyro_parasitic = st.slider("Pyro Parasitic (%)", 0.0, 1.0, 0.15, 0.01)
            
        with col_env4:
            st.markdown("**WtE Incinerator Metrics**")
            wte_elec_yield = st.number_input("WtE Yield (MWh/ton)", value=0.60, format="%.2f")
            wte_avoidance = st.number_input("WtE Methane Avoidance", value=1.00, format="%.2f")
            wte_fossil_ef = st.number_input("Fossil Stack EF", value=0.35, format="%.2f")
            wte_parasitic = st.slider("WtE Parasitic (%)", 0.0, 1.0, 0.12, 0.01)

        if calc_ad and ad_tpd_total > 0:
            M_ad = ad_tpd_total * 330 
            e_avoid_ad = M_ad * doc_avg_base * doc_f * mcf * f_ch4 * (16/12) * gwp_ch4
            e_offset_ad = (M_ad * ad_elec_yield) * ef_grid
            e_plant_ad = e_offset_ad * ad_parasitic
            total_ad_co2 = e_avoid_ad + e_offset_ad - e_plant_ad
                
        if calc_pyro and plastic_tpd_to_pyro > 0:
            M_pyro = plastic_tpd_to_pyro * 330
            e_fuel_pyro = M_pyro * pyro_oil_yield * pyro_fuel_offset
            e_offset_pyro = (M_pyro * pyro_elec_yield) * ef_grid
            e_plant_pyro = e_offset_pyro * pyro_parasitic
            total_pyro_co2 = e_fuel_pyro + e_offset_pyro - e_plant_pyro
            
        if calc_wte and final_wte_tpd > 0:
            M_wte = final_wte_tpd * 330
            e_avoid_wte = M_wte * wte_avoidance
            e_offset_wte = (M_wte * wte_elec_yield) * ef_grid
            e_stack_fossil = M_wte * wte_fossil_ef
            e_plant_wte = e_offset_wte * wte_parasitic
            total_wte_co2 = e_avoid_wte + e_offset_wte - e_plant_wte - e_stack_fossil

        grand_total_co2 = total_ad_co2 + total_pyro_co2 + total_wte_co2
        
        st.divider()
        st.markdown("<h2 style='text-align: center; color: #2e7d32;'>🌱 Total Plant Carbon Reduction</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{grand_total_co2:,.0f} Metric Tons CO2e / Year</h1>", unsafe_allow_html=True)
        st.divider()

        if calc_ad and ad_tpd_total > 0:
            st.markdown(f"### 🟢 AD Carbon Reduction: **{total_ad_co2:,.0f} tons CO2e**")
            res1, res2, res3 = st.columns(3)
            res1.metric("Avoided Methane", f"+ {e_avoid_ad:,.0f} tCO2e")
            res2.metric("Grid Offset (Biogas)", f"+ {e_offset_ad:,.0f} tCO2e")
            res3.metric("AD Parasitic Load", f"- {e_plant_ad:,.0f} tCO2e")
            
        if calc_pyro and plastic_tpd_to_pyro > 0:
            st.markdown(f"### 🟣 Pyrolysis Carbon Reduction: **{total_pyro_co2:,.0f} tons CO2e**")
            p1, p2, p3 = st.columns(3)
            p1.metric("Fuel Displacement", f"+ {e_fuel_pyro:,.0f} tCO2e")
            p2.metric("Grid Offset (CHP)", f"+ {e_offset_pyro:,.0f} tCO2e")
            p3.metric("Pyro Parasitic Load", f"- {e_plant_pyro:,.0f} tCO2e")
            
        if calc_wte and final_wte_tpd > 0:
            st.markdown(f"### 🔴 WtE Incinerator Carbon Reduction: **{total_wte_co2:,.0f} tons CO2e**")
            w1, w2, w3, w4 = st.columns(4)
            w1.metric("Avoided Methane", f"+ {e_avoid_wte:,.0f} tCO2e")
            w2.metric("Grid Offset (Turbine)", f"+ {e_offset_wte:,.0f} tCO2e")
            w3.metric("Direct Stack Emissions", f"- {e_stack_fossil:,.0f} tCO2e")
            w4.metric("WtE Parasitic Load", f"- {e_plant_wte:,.0f} tCO2e")

        st.divider()
        with st.expander("📐 View Sample Calculations & Engineering References"):
            if tutorial_mode:
                st.info("💡 **Documentation:** This section proves that your math isn't just a guess. It cites the specific formulas and page numbers used to build the tool.")
            st.markdown("""
            ### Document Baseline References
            All primary equipment assumptions are derived directly from the **HSSI-Isabela Preliminary Techno Commercial Proposal (Nov 2025)**:
            * **Total Capacity:** 350 TPD (Page 3)
            * **AD Plant:** 150 TPD generating approx. 1.4 MW (Page 5)
            * **Pyrolysis Plant:** 20 TPD generating 9,000 Liters of oil and 1.6 MW (Page 5)
            * **WtE Plant:** 120 TPD generating approx. 3.0 MW (Page 5)
            """)
