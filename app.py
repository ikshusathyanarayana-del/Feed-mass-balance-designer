import streamlit as st
import graphviz
import pandas as pd

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Isabela MRF FEED Designer", layout="wide")
st.title("⚙️ Isabela MRF Waste-to-Energy Plant Designer")
st.markdown("Dynamic mass balance tool replicating the exact process flow, machine efficiencies, and screw press dewatering logic of the Mutiara Etnik FEED spreadsheet.")

# ==========================================
# UI: SIDEBAR INPUTS
# ==========================================
st.sidebar.header("1. Operational Input")
capacity_tpd = st.sidebar.number_input("Plant Capacity (TPD)", min_value=10, max_value=5000, value=350, step=10)

st.sidebar.header("2. Client Preferences")
pref_tech = st.sidebar.multiselect(
    "Preferred Technology",
    options=['WtE', 'AD', 'Pyrolysis'],
    default=['WtE', 'AD', 'Pyrolysis']
)

# --- EXPANDER 3: COMPOSITION ---
with st.sidebar.expander("📊 3. Waste Composition (%)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        food_waste = st.number_input("Food", value=51.27, step=1.0)
        garden_waste = st.number_input("Garden", value=15.89, step=1.0)
        plastics = st.number_input("Plastics", value=15.54, step=1.0)
        paper = st.number_input("Paper", value=6.73, step=1.0)
        textile = st.number_input("Textile", value=2.04, step=1.0)
        leachate = st.number_input("Leachate", value=15.00, step=1.0)
    with col2:
        pampers = st.number_input("Pampers", value=4.10, step=1.0)
        wood = st.number_input("Wood", value=0.18, step=0.1)
        inerts = st.number_input("Inerts", value=1.79, step=1.0)
        ferrous = st.number_input("Ferrous", value=0.60, step=0.1)
        non_ferrous = st.number_input("Non-Ferrous", value=0.38, step=0.1)
        bulky = st.number_input("Bulky", value=1.97, step=0.1)

# --- EXPANDER 4: MACHINE EFFICIENCIES ---
with st.sidebar.expander("⚙️ 4. Machine Efficiencies (%)", expanded=False):
    eff_nir = st.slider("NIR Sorter (Plastics)", 0, 100, 50) 
    eff_trommel = st.slider("Trommel (Organics)", 0, 100, 62) 
    eff_mag = st.slider("Magnetic Sep (Ferrous)", 0, 100, 100)
    eff_manual = st.slider("Manual Sorting (Inerts & NF)", 0, 100, 100) 

# --- EXPANDER 5: MOISTURE CONTENT ---
with st.sidebar.expander("💧 5. Moisture Content (% Dry Material)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        dry_food = st.number_input("Food Dry %", value=15.0) / 100.0
        dry_garden = st.number_input("Garden Dry %", value=15.0) / 100.0
        dry_plastics = st.number_input("Plastics Dry %", value=100.0) / 100.0
        dry_paper = st.number_input("Paper Dry %", value=80.0) / 100.0
        dry_textile = st.number_input("Textile Dry %", value=50.0) / 100.0
    with col2:
        dry_pampers = st.number_input("Pampers Dry %", value=50.0) / 100.0
        dry_wood = st.number_input("Wood Dry %", value=80.0) / 100.0
        dry_inerts = st.number_input("Inerts Dry %", value=100.0) / 100.0
        dry_ferrous = st.number_input("Ferrous Dry %", value=100.0) / 100.0
        dry_non_ferrous = st.number_input("Non-Ferrous Dry %", value=100.0) / 100.0

# --- EXPANDER 6: CALORIFIC VALUES ---
with st.sidebar.expander("🔥 6. Calorific Values (Kcal/kg)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        cv_food = st.number_input("Food CV", value=1200, step=100)
        cv_garden = st.number_input("Garden CV", value=1200, step=100)
        cv_plastics = st.number_input("Plastics CV", value=3300, step=100)
        cv_paper = st.number_input("Paper CV", value=3585, step=100)
        cv_textile = st.number_input("Textile CV", value=3871, step=100)
    with col2:
        cv_pampers = st.number_input("Pampers CV", value=1840, step=100)
        cv_wood = st.number_input("Wood CV", value=3100, step=100)
        cv_inerts = st.number_input("Inerts CV", value=0, step=100)
        cv_ferrous = st.number_input("Ferrous CV", value=0, step=100)
        cv_non_ferrous = st.number_input("Non-Ferrous CV", value=0, step=100)

# ==========================================
# DATA COMPILATION
# ==========================================
materials = {
    'Food_Waste': {'pct': food_waste, 'dry_frac': dry_food, 'cv': cv_food},
    'Garden_Waste': {'pct': garden_waste, 'dry_frac': dry_garden, 'cv': cv_garden},
    'Plastics': {'pct': plastics, 'dry_frac': dry_plastics, 'cv': cv_plastics},
    'Paper_Cardboard': {'pct': paper, 'dry_frac': dry_paper, 'cv': cv_paper},
    'Textile': {'pct': textile, 'dry_frac': dry_textile, 'cv': cv_textile},
    'Pampers': {'pct': pampers, 'dry_frac': dry_pampers, 'cv': cv_pampers},
    'Wood': {'pct': wood, 'dry_frac': dry_wood, 'cv': cv_wood},
    'Inerts': {'pct': inerts, 'dry_frac': dry_inerts, 'cv': cv_inerts},
    'Ferrous': {'pct': ferrous, 'dry_frac': dry_ferrous, 'cv': cv_ferrous},
    'Non_Ferrous': {'pct': non_ferrous, 'dry_frac': dry_non_ferrous, 'cv': cv_non_ferrous},
    'Leachate': {'pct': leachate, 'dry_frac': 0.0, 'cv': 0},
    'Bulky': {'pct': bulky, 'dry_frac': 1.0, 'cv': 0}
}

total_input_pct = sum(m['pct'] for m in materials.values())
if total_input_pct > 100.1 or total_input_pct < 99.9:
    st.warning(f"⚠️ **Note:** Your composition adds up to {total_input_pct:.2f}%. Ideally it should equal exactly 100%.")

# ==========================================
# CORE ENGINEERING LOGIC
# ==========================================
def run_mass_balance():
    DAYS_PER_YEAR = 330
    HOURS_PER_DAY = 10.0

    stream = {}
    for name, props in materials.items():
        tpd = (props['pct'] / 100.0) * capacity_tpd
        dry_tpd = tpd * props['dry_frac']
        stream[name] = {'tpd': tpd, 'dry_tpd': dry_tpd, 'cv': props['cv']}

    dot = graphviz.Digraph(comment='Excel Replica Mass Balance', format='png')
    dot.attr(rankdir='TB', nodesep='0.6', ranksep='0.8')
    dot.attr('node', shape='none', fontname='Helvetica', fontsize='9')
    mass_balance_data = []

    def make_mb_node(node_id, title, bgcolor, tpd, dry_tpd, capacity_ref=capacity_tpd):
        if tpd <= 0.01: return None
        safe_title = title.replace('&', '&amp;')
        pct_total = (tpd / capacity_ref) * 100.0
        tpy = tpd * DAYS_PER_YEAR
        tph = tpd / HOURS_PER_DAY
        dry_pct = (dry_tpd / tpd) * 100.0 if tpd > 0 else 0
        wet_pct = 100.0 - dry_pct
        dry_tpy = dry_tpd * DAYS_PER_YEAR
        wet_tpy = tpy - dry_tpy
        
        mass_balance_data.append({
            "Process Node": title, "Tons/Day": round(tpd, 2), "Tons/Year": round(tpy, 0),
            "% Dry": f"{dry_pct:.2f}%", "% Wet": f"{wet_pct:.2f}%"
        })
        
        html = f"""<
        <TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
            <TR><TD COLSPAN="4" BGCOLOR="{bgcolor}"><B>{safe_title}</B></TD></TR>
            <TR><TD>{pct_total:.2f}%</TD><TD>{tpy:,.0f} Tons/Year</TD><TD>Dry Material:</TD><TD>Wet :</TD></TR>
            <TR><TD>330 Days/Year</TD><TD>{tpd:,.2f} Tons/Day</TD><TD>{dry_pct:.2f}%</TD><TD>{wet_pct:.2f}%</TD></TR>
            <TR><TD>10.00 Hour/Day</TD><TD>{tph:,.2f} Tons / Hour</TD><TD>{dry_tpy:,.0f} Tons/Year</TD><TD>{wet_tpy:,.0f} Tons/Year</TD></TR>
        </TABLE>>"""
        dot.node(node_id, html)
        return tpd

    def current_stream_totals():
        return sum(s['tpd'] for s in stream.values()), sum(s['dry_tpd'] for s in stream.values())

    # --- 1. RECEPTION ---
    curr_tpd, curr_dry = current_stream_totals()
    make_mb_node('Reception', 'RECEPTION OF MATERIAL (HOPPER)', '#c5e0b4', curr_tpd, curr_dry)
    spine = 'Reception'

    # --- 2. BAG OPENER (Extracts Leachate and Bulky) ---
    if stream['Leachate']['tpd'] > 0 or stream['Bulky']['tpd'] > 0:
        make_mb_node('BagOpener', 'BAG OPENER', '#b4c6e7', curr_tpd, curr_dry)
        dot.edge(spine, 'BagOpener', color='#4f81bd', penwidth='3')
        spine = 'BagOpener'
        
        if stream['Leachate']['tpd'] > 0:
            make_mb_node('Leachate', 'LEACHATE', '#ededed', stream['Leachate']['tpd'], stream['Leachate']['dry_tpd'])
            dot.edge(spine, 'Leachate', label='Liquid', color='#4f81bd', penwidth='2')
            stream['Leachate']['tpd'] = 0 
            stream['Leachate']['dry_tpd'] = 0
            
        if stream['Bulky']['tpd'] > 0:
            make_mb_node('Bulky', 'BULKY MATERIALS', '#f8cbad', stream['Bulky']['tpd'], stream['Bulky']['dry_tpd'])
            dot.edge(spine, 'Bulky', label='Bulky', color='#4f81bd', penwidth='2')
            stream['Bulky']['tpd'] = 0 
            stream['Bulky']['dry_tpd'] = 0
            
        curr_tpd, curr_dry = current_stream_totals()

    # --- 3. MAGNETIC SEPARATOR ---
    if stream['Ferrous']['tpd'] > 0:
        make_mb_node('MagSep', 'MAGNETIC SEPARATOR', '#ccc1da', curr_tpd, curr_dry)
        dot.edge(spine, 'MagSep', color='#4f81bd', penwidth='3')
        spine = 'MagSep'
        
        rec_fe = stream['Ferrous']['tpd'] * (eff_mag / 100.0)
        rec_fe_dry = stream['Ferrous']['dry_tpd'] * (eff_mag / 100.0)
        make_mb_node('Ferrous', 'FERROUS MATERIAL', '#f8cbad', rec_fe, rec_fe_dry)
        dot.edge(spine, 'Ferrous', color='#4f81bd', penwidth='2')
        stream['Ferrous']['tpd'] -= rec_fe
        stream['Ferrous']['dry_tpd'] -= rec_fe_dry
        curr_tpd, curr_dry = current_stream_totals()

    # --- 4. TROMMEL & SCREW PRESS (Organics) ---
    org_tpd = stream['Food_Waste']['tpd'] + stream['Garden_Waste']['tpd']
    if org_tpd > 0 and 'AD' in pref_tech:
        make_mb_node('Trommel', 'SPLITTER / SCREW SCREEN / TROMMEL', '#e2efda', curr_tpd, curr_dry)
        dot.edge(spine, 'Trommel', color='#4f81bd', penwidth='3')
        spine = 'Trommel'
        
        rec_org_tpd = org_tpd * (eff_trommel / 100.0)
        rec_org_dry = (stream['Food_Waste']['dry_tpd'] + stream['Garden_Waste']['dry_tpd']) * (eff_trommel / 100.0)
        
        make_mb_node('Organics', 'ORGANICS', '#f8cbad', rec_org_tpd, rec_org_dry)
        dot.edge(spine, 'Organics', color='#4f81bd', penwidth='2')
        
        # SCREW PRESS LOGIC: Mechanically pushes Dry % to 40%
        screw_press_dry_target = 0.40
        new_total_mass_after_press = rec_org_dry / screw_press_dry_target
        make_mb_node('ScrewPress', 'ORGANICS - SCREW PRESS / AD', '#ededed', new_total_mass_after_press, rec_org_dry)
        dot.edge('Organics', 'ScrewPress', color='#4f81bd', penwidth='2')
        
        # Deduct the captured organics from the main stream
        for key in ['Food_Waste', 'Garden_Waste']:
            stream[key]['tpd'] *= (1 - (eff_trommel / 100.0))
            stream[key]['dry_tpd'] *= (1 - (eff_trommel / 100.0))
        curr_tpd, curr_dry = current_stream_totals()

    # --- 5. MANUAL SORTING (Combines Inerts & Non-Ferrous) ---
    if stream['Inerts']['tpd'] > 0 or stream['Non_Ferrous']['tpd'] > 0:
        make_mb_node('ManualSort', 'MANUAL SORTING STATION & SDS', '#fce4d6', curr_tpd, curr_dry)
        dot.edge(spine, 'ManualSort', color='#4f81bd', penwidth='3')
        spine = 'ManualSort'
        
        rec_inerts = stream['Inerts']['tpd'] * (eff_manual / 100.0)
        rec_inerts_dry = stream['Inerts']['dry_tpd'] * (eff_manual / 100.0)
        rec_nf = stream['Non_Ferrous']['tpd'] * (eff_manual / 100.0)
        rec_nf_dry = stream['Non_Ferrous']['dry_tpd'] * (eff_manual / 100.0)
        
        total_rec_inf = rec_inerts + rec_nf
        total_rec_inf_dry = rec_inerts_dry + rec_nf_dry
        
        make_mb_node('InertsNF', 'INERTS & NON-FERROUS REJECTS', '#f8cbad', total_rec_inf, total_rec_inf_dry)
        dot.edge(spine, 'InertsNF', color='#4f81bd', penwidth='2')
        
        stream['Inerts']['tpd'] -= rec_inerts
        stream['Inerts']['dry_tpd'] -= rec_inerts_dry
        stream['Non_Ferrous']['tpd'] -= rec_nf
        stream['Non_Ferrous']['dry_tpd'] -= rec_nf_dry
        curr_tpd, curr_dry = current_stream_totals()

    # --- 6. NIR OPTICAL SORTING ---
    if stream['Plastics']['tpd'] > 0 and 'Pyrolysis' in pref_tech:
        make_mb_node('NIR', 'NIR (OPTICAL SORTING)', '#fff2cc', curr_tpd, curr_dry)
        dot.edge(spine, 'NIR', color='#4f81bd', penwidth='3')
        spine = 'NIR'
        
        rec_plas = stream['Plastics']['tpd'] * (eff_nir / 100.0)
        rec_plas_dry = stream['Plastics']['dry_tpd'] * (eff_nir / 100.0)
        make_mb_node('Plastics', 'PLASTICS TO PYRO PLANT', '#f8cbad', rec_plas, rec_plas_dry)
        dot.edge(spine, 'Plastics', color='#4f81bd', penwidth='2')
        stream['Plastics']['tpd'] -= rec_plas
        stream['Plastics']['dry_tpd'] -= rec_plas_dry
        curr_tpd, curr_dry = current_stream_totals()

    # --- 7. WtE PLANT ---
    wte_energy_data = []
    total_kcal = 0

    if curr_tpd > 0.01:
        make_mb_node('WtE', 'WtE PLANT', '#a9d18e', curr_tpd, curr_dry)
        dot.edge(spine, 'WtE', color='#4f81bd', penwidth='4')
        
        for name, data in stream.items():
            if data['tpd'] > 0.01:
                component_kcal = data['tpd'] * data['cv']
                total_kcal += component_kcal
                wte_energy_data.append({
                    "Material": name.replace('_', ' '),
                    "Tons/Day to WtE": round(data['tpd'], 2),
                    "CV (Kcal/kg)": data['cv']
                })
                
    avg_cv_kcal = (total_kcal / curr_tpd) if curr_tpd > 0 else 0
    avg_cv_mj = avg_cv_kcal * 0.004184

    return dot, mass_balance_data, wte_energy_data, avg_cv_kcal, avg_cv_mj, curr_tpd

# ==========================================
# RENDER UI
# ==========================================
diagram, mb_data, wte_data, avg_cv_kcal, avg_cv_mj, final_wte_tpd = run_mass_balance()

st.subheader("Process Flow & Dynamic Mass Balance")
st.graphviz_chart(diagram, use_container_width=True)

st.divider()

st.subheader("🔥 WtE Energy & Calorific Value Analysis")
st.markdown("Calculates the specific Calorific Value of the final residual mix entering the WtE plant based on custom CV and efficiency variables.")

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
    st.download_button("📥 Download Mass Balance Data", data=csv, file_name="isabela_mass_balance.csv", mime="text/csv")
