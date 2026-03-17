"""
Created on Tue Oct 17 15:17:06 2023

@author: joshu
"""

## This code creates a Streamlit dashboard for county economic data, allowing users to select a state and county to view various economic metrics and trends.

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

st.set_page_config(page_title="Hello", page_icon="🚚",layout='wide')
streamlit_style = """
			<style>
			@import url('https://fonts.googleapis.com/css2?family=Roboto, sans-serif:wght@100&display=swap');

			html, body, [class*="css"]  {
			font-family: 'Roboto, sans-serif', sans-serif;
			}
			</style>
			"""
st.markdown(streamlit_style, unsafe_allow_html=True)


### initialize all inputs/variables

@st.cache_data  # This function will be cached to optimize loading
def load_data():
    path1 = "county_all_vars_index.dta"
    path2 = "county_all_vars_post_index.csv"
    path3 = "cbp_county_2016.csv"
    path4 = "cbp_county_2016_all_tradserv_emp.csv"
    return pd.read_stata(path1), pd.read_csv(path2), pd.read_csv(path3), pd.read_csv(path4)

national_df, long_df, cbp_df, tradserv_df = load_data()
default_state = "NC"
default_county = "Durham County, NC"

sorted_states = np.sort(national_df['state'].unique())
try:
    default_index_st = int(np.where(sorted_states == default_state)[0][0])
except IndexError:
    default_index_st = 0

st.sidebar.write('### Select County')
state = st.sidebar.selectbox("State", sorted_states, index=default_index_st)
national_df = national_df[national_df["state"] == state]

sorted_counties = np.sort(national_df['county_name'].unique())
try:
    default_index_co = int(np.where(sorted_counties == default_county)[0][0])
except IndexError:
    default_index_co = 0

county = st.sidebar.selectbox("County", sorted_counties, index=default_index_co)

county_df = national_df[national_df["county_name"]==county]
county_long_df = long_df[long_df["county_name"]==county]
county_id = county_df["countyid"].iloc[0]
county_cbp_df = cbp_df[(cbp_df["countyid"] == county_id)& (cbp_df['emp']> 1.)]
_tradserv_row = tradserv_df[tradserv_df["countyid"] == county_id]
tradserv_emp = _tradserv_row["emp"].iloc[0] if len(_tradserv_row) > 0 else 0
total_emp_2016 = cbp_df[cbp_df["countyid"] == county_id]["emp"].sum()
tradserv_pct = round(100 * tradserv_emp / total_emp_2016, 1) if total_emp_2016 > 0 else 0

_cbp_all = cbp_df[cbp_df["countyid"] == county_id]
mfg_emp_2016 = round(_cbp_all[(_cbp_all["sic87dd"] >= 2000) & (_cbp_all["sic87dd"] <= 3999)]["emp"].sum(), 0)
mfg_pct_2016 = round(100 * mfg_emp_2016 / total_emp_2016, 1) if total_emp_2016 > 0 else 0

_long_2022 = county_long_df[county_long_df["year"] == county_long_df["year"].max()]
total_jobs_2022 = round(_long_2022["employed_workers"].iloc[0], 0) if len(_long_2022) > 0 else 0
college_jobs_2022 = round(_long_2022["employed_college"].iloc[0], 0) if len(_long_2022) > 0 else 0
noncollege_jobs_2022 = round(_long_2022["employed_STARs"].iloc[0], 0) if len(_long_2022) > 0 else 0

# -----------------------------
# Compute stats
# -----------------------------
def simple_stats(co_df):

    star_wage = round(co_df["star_median2022"].iloc[0] , 0)
    college_wage = round(co_df["college_wage2022"].iloc[0], 0)

    star_emp = round(co_df["STAR_emp_rate2022"].iloc[0], 2)
    college_emp = round(co_df["emp_rate_college2022"].iloc[0], 2)

    pct_educ2022 = round(100 * co_df["educ_pct_total_stloc2022"].iloc[0], 2)
    ppupil_educ2022 = round(co_df["spend_ppupil_2022"].iloc[0], 0)

    job_loss = round(co_df["pred_emp_loss"].iloc[0], 0)
    job_gain = round(co_df["pred_emp_gain"].iloc[0], 0)

    mfgemp_loss = max(
        0,
        round(co_df["mfgsh1991"].iloc[0]*co_df["employed_workers1990"].iloc[0] - co_df["mfgemp2011"].iloc[0], 0)
    )

    serv_exp_job = round(co_df["tradserv_exp_emp_2017_2022"].iloc[0], 0)

    return (
        star_wage, college_wage, star_emp, college_emp,
        pct_educ2022, ppupil_educ2022,
        job_loss, job_gain, mfgemp_loss, serv_exp_job
    )

stats = simple_stats(county_df)

(
    star_wage, all_wage, star_emp, college_emp,
    pct_educ2022, ppupil_educ2022,
    job_loss, job_gain, mfgemp_loss, serv_exp_job
) = stats


# -----------------------------
# Dashboard
# -----------------------------
st.title("County Economic Dashboard")
st.subheader(f"{county} County Overview")
st.caption("Wage data in in $2026. Non-college workers includes workers with a high school diploma but no four-year college degree.")

_COLORS = {
    "red":     ("#FDF2F2", "#B85C5C"),
    "green":   ("#F2F7F3", "#4A8A57"),
    "purple":  ("#F3F2FA", "#6B62C0"),
    "orange":  ("#FDF6EE", "#C07A38"),
    "neutral": ("#F7F7F8", "#888888"),
}

def cmetric(label, value, style="neutral"):
    bg, accent = _COLORS[style]
    st.markdown(
        f'<div style="background:{bg};border-left:3px solid {accent};'
        f'padding:10px 14px;border-radius:4px;margin-bottom:5px;">'
        f'<div style="font-size:11px;color:#666;letter-spacing:0.4px;text-transform:uppercase;margin-bottom:3px;">{label}</div>'
        f'<div style="font-size:20px;font-weight:600;color:#1a1a1a;letter-spacing:-0.3px;">{value}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

# metrics
st.metric("Total Employed Workers (2022)", f"{total_jobs_2022:,.0f}")

col1, col2 = st.columns(2)

# Row 1: Non-college | College
with col1: cmetric("Non-College Educated Employed Workers (2022)", f"{noncollege_jobs_2022:,.0f}", "purple")
with col2: cmetric("College Educated Employed Workers (2022)", f"{college_jobs_2022:,.0f}", "orange")

# Row 2: Wages
with col1: cmetric("Non-College Median Wage (2022)", f"${star_wage:,.0f}", "purple")
with col2: cmetric("College Median Wage (2022)", f"${all_wage:,.0f}", "orange")

# Row 3: Employment rates
with col1: cmetric("Non-College Employment Rate (2022)", f"{star_emp}%", "purple")
with col2: cmetric("College Employment Rate (2022)", f"{college_emp}%", "orange")

# Row 4: Tradable services
with col1: cmetric("Tradable Services Employment (2016)", f"{tradserv_emp:,.0f}")
with col2: cmetric("Tradable Services Share of Employment (2016)", f"{tradserv_pct}%")

# Row 5: Manufacturing (2016)
with col1: cmetric("Manufacturing Employment (2016)", f"{mfg_emp_2016:,.0f}")
with col2: cmetric("Manufacturing Share of Employment (2016)", f"{mfg_pct_2016}%")

# Row 6: Education spending
with col1: cmetric("Education Spending (% local budget)", f"{pct_educ2022}%")
with col2: cmetric("Per-Pupil Spending", f"${ppupil_educ2022:,.0f}")

# Row 7: Mfg jobs lost | Services jobs gained (same 1991–2011 period; not available)
with col1: cmetric("Manufacturing Jobs Lost (1991–2011)", f"{mfgemp_loss:,.0f}", "red")
with col2: cmetric("Services Jobs Gained (1991–2011)", "N/A", "green")

# Row 8: Total estimated job flows
with col1: cmetric("Est. Job Loss from Low-Wage Manuf. Imports (1991–2011)", f"{job_loss:,.0f}", "red")
with col2: cmetric("Est. Job Gain from Manuf. Exports & Inputs (2011–2022)", f"{job_gain:,.0f}", "green")

# Row 9: Annualized job flows (20yr import shock; 11yr export gain)
with col1: cmetric("Annualized Est. Job Loss from Low-Wage Imports (1991–2011)", f"{job_loss/20:,.0f}", "red")
with col2: cmetric("Annualized Est. Job Gain from Exports & Inputs (2011–2022)", f"{job_gain/11:,.0f}", "green")

# Row 10: Tradable service job growth from exports
with col1: cmetric("Est. Job Growth from Tradable Service Exports (2017–2022)", f"{serv_exp_job:,.0f}", "green")
with col2: cmetric("Annualized Est. Job Growth from Tradable Service Exports (2017–2022)", f"{serv_exp_job/5:,.0f}", "green")

### INDUSTRY TABLE
county_cbp_df["l_m_dw_uswld_2023"] = county_cbp_df["l_m_dw_uswld_2023"].round(1)
st.subheader("Industries by Employment")
_table_cols = ["sic87dd_desc", "emp","l_m_dw_uswld_2023"]
industry_table = (
    county_cbp_df[_table_cols]
    .sort_values("emp", ascending=False)
    .rename(columns={
        "sic87dd_desc": "Industry",
        "emp": "Employment",
        "l_m_dw_uswld_2023": "Est. Imported Inputs Benefit (0-25)"
    })
    .reset_index(drop=True)
)
industry_table["Employment"] = industry_table["Employment"].apply(lambda x: f"{x:,.0f}")

# Faux columns seeded by county for consistency
_rng = np.random.default_rng(int(county_id) + 42)
n = len(industry_table)
industry_table["Non-College Workers"] = (
    county_cbp_df.sort_values("emp", ascending=False)["emp"].values
    * _rng.uniform(0.52, 0.82, n)
).astype(int).astype(str)
industry_table["Non-College Workers ⚠"] = [f"{int(v):,}" for v in
    county_cbp_df.sort_values("emp", ascending=False)["emp"].values * _rng.uniform(0.52, 0.82, n)]
growth = _rng.uniform(-9, 18, n)
industry_table["Job Growth (%) ⚠"] = [f"{v:+.1f}%" for v in growth]
unfilled = (
    county_cbp_df.sort_values("emp", ascending=False)["emp"].values
    * _rng.uniform(0.03, 0.13, n)
).astype(int)
industry_table["Unfilled Positions ⚠"] = [f"{v:,}" for v in unfilled]
wages = _rng.integers(28000, 92000, n)
industry_table["Median Wage ⚠"] = [f"${v:,}" for v in wages]

st.dataframe(industry_table, use_container_width=True, hide_index=True)
st.caption("Using 2016 Employment, 2023 Imports, and 1992 Input-Output Table. ⚠ Columns marked ⚠ show illustrative placeholder data.")

### OPPORTUNITY OCCUPATION TABLE
st.subheader("Non-College Educated Opportunity Occupations")

_OCC_DATA = [
    ("Registered Nurse",         "Healthcare",  77_400, 6,   15, 12),
    ("Heavy Truck Driver",        "Transportation / Warehousing", 48_300, 4,  85, 68),
    ("Electrician",               "Construction / Manufacturing", 57_200, 11, 84, 41),
    ("Software Developer",        "Professional Services / Finance", 121_000, 25, 9, 74),
    ("Welder",                    "Manufacturing", 44_100, 3,  91, 79),
    ("Construction Laborer",      "Construction", 38_600, 5,  90, 22),
    ("Machinist",                 "Manufacturing", 47_300, 7,  86, 81),
    ("Medical Assistant",         "Healthcare",  36_200, 16, 58, 8),
    ("HVAC Technician",           "Construction / Building Services", 52_700, 9, 83, 30),
    ("Logistics Coordinator",     "Wholesale Trade / Transportation", 50_100, 8, 72, 61),
    ("Customer Service Rep",      "Retail / Finance / Healthcare", 35_800, -4, 69, 35),
    ("Industrial Engineer",       "Manufacturing / Consulting", 92_000, 10, 18, 77),
]

_occ_rng = np.random.default_rng(int(county_id) + 99)
occ_rows = []
for occ, industries, wage, growth_pct, noncoll_pct, global_pct in _OCC_DATA:
    jobs_now = int(_occ_rng.integers(200, 4000))
    occ_rows.append({
        "Occupation":                     occ,
        "Jobs (County Est.) ⚠":           f"{jobs_now:,}",
        "Projected Growth (%) ⚠":         f"{growth_pct:+d}%",
        "Common Industries":              industries,
        "Median Wage ⚠":                  f"${wage:,}",
        "% Non-College Workers ⚠":        f"{noncoll_pct}%",
        "% in Globally Exposed Inds. ⚠":  f"{global_pct}%",
    })

occ_df = pd.DataFrame(occ_rows)
st.dataframe(occ_df, use_container_width=True, hide_index=True)
st.caption("⚠ Columns marked ⚠ show illustrative placeholder data.")

### DIVISION PIE CHART
def sic_division(code):
    if   100  <= code <= 999:  return "Agriculture, Forestry & Fishing"
    elif 1000 <= code <= 1499: return "Mining"
    elif 1500 <= code <= 1799: return "Construction"
    elif 2000 <= code <= 3999: return "Manufacturing"
    elif 4000 <= code <= 4999: return "Transportation, Communications & Utilities"
    elif 5000 <= code <= 5199: return "Wholesale Trade"
    elif 5200 <= code <= 5999: return "Retail Trade"
    elif 6000 <= code <= 6799: return "Finance, Insurance & Real Estate"
    elif 7000 <= code <= 8999: return "Services"
    elif 9100 <= code <= 9729: return "Public Administration"
    else:                      return "Other"

div_df = county_cbp_df.copy()
div_df["division"] = div_df["sic87dd"].apply(sic_division)
div_agg = div_df.groupby("division")["emp"].sum().reset_index()
div_agg = div_agg[div_agg["emp"] > 0].sort_values("emp", ascending=False)


fig_pie = go.Figure(go.Pie(
    labels=div_agg["division"],
    values=div_agg["emp"],
    hole=0.3,
    textinfo="percent",
    textfont=dict(size=13, color="white", family="Roboto, sans-serif"),
    insidetextorientation="radial",
))
fig_pie.update_layout(
    title=dict(
        text="Employment by Industry Division (2016)",
        x=0.5, xanchor="center",
        font=dict(size=18, color="black", family="Roboto, sans-serif")
    ),
    showlegend=True,
    legend=dict(
        font=dict(size=13, color="black", family="Roboto, sans-serif"),
        bgcolor="white",
        bordercolor="black",
        borderwidth=1,
        x=1.02,
        xanchor="left",
        y=0.5,
        yanchor="middle",
    ),
    paper_bgcolor="#F4F4F4",
    margin=dict(t=60, b=20, l=20, r=220),
)
st.plotly_chart(fig_pie, use_container_width=True)

### GRAPHS
def employment_trends(county_df):

    years = county_df["year"]
    county_emp = county_df["star_emp_rate"]
    peer_emp = county_df["star_emp_rate_qpop_avg"]
    name = county_df['name_short'].iloc[0]

    fig3 = make_subplots(specs=[[{"secondary_y": False}]])

    fig3.update_layout(
        width=900,
        title={
            'text': f"Change in Non-College Employment Rate in <br> {name} vs Similar-Sized Counties",
            'x': 0.5,
            'y': 0.94,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=21, color="black", family="Roboto, sans-serif"),
        },

        xaxis=dict(
            title=dict(text='Year', font=dict(color='black', size=20, family="Roboto Medium, sans-serif")),
            range=[1990, 2023],
            dtick=5,
            title_standoff=30,
            ticklabelposition="outside right",
            tickfont=dict(color='black', size=20, family="Roboto, sans-serif"),
        ),

        yaxis=dict(
            title=dict(text='Non-College<br>Employment Rate (%)', font=dict(color='black', size=20, family="Roboto Medium, sans-serif")),
            dtick = 2,
            range=[min(min(county_emp),min(peer_emp))-2,max(max(county_emp),max(peer_emp))+2],
            title_standoff=25,
            tickfont=dict(color='black', size=18, family="Roboto, sans-serif"),
        ),

        margin=dict(t=105, r=0, l=155, b=100),

        legend=dict(
            font=dict(size=14, color="black"),
            x=.35,
            xanchor='right',
            y=.35,
            yanchor='top',
            bgcolor='#ECECEC',
            bordercolor='black',
            borderwidth=1
        ),

        paper_bgcolor='#F4F4F4',
        plot_bgcolor='#F4F4F4',
    )
    # Import Shock shaded region
    fig3.add_shape(
        x0=2000.,
        x1=2011.,
        y0=math.ceil(min(min(county_emp),min(peer_emp))-2),
        y1=max(max(county_emp),max(peer_emp))+2,
        fillcolor="gray",
        opacity=0.15,
        line_width=0,
        layer="below",
    )
    
    fig3.add_annotation(
        x=2005.5,
        y=0.04,
        xref="x",
        yref="paper",
        text="Import Shock",
        showarrow=False,
        font=dict(size=14, color='black')
    )

    # County line
    fig3.add_trace(
        go.Scatter(
            x=years,
            y=county_emp,
            mode='lines',
            line=dict(color='#F7A072', width=3),
            name=name
        )
    )

    # Peer counties line
    fig3.add_trace(
        go.Scatter(
            x=years,
            y=peer_emp,
            mode='lines',
            line=dict(color='#445E93', width=3),
            name='Similar Counties'
        )
    )

    st.plotly_chart(fig3,  width='stretch')

employment_trends(county_long_df)

def county_dual_axis_chart(df):
    df = df.copy()
    name = df['name_short'].iloc[0]

    fig = make_subplots(specs=[[{"secondary_y": False}]])

    fig.update_layout(
        width=900,
        title={'text': f"Change in Manufacturing Jobs, and Good-Paying Jobs, <br> for Non-College Workers in {name}",
               'x':0.5,
               'y':0.94,
               'xanchor':'center',
               'font': dict(size=21, color="black", family="Roboto, sans-serif")},


        xaxis=dict(
            title=dict(text="Year", font=dict(color='black', size=20, family="Roboto Medium, sans-serif")),
            range=[1990,2022],
            dtick=5,
            tickfont=dict(color='black', size=20, family="Roboto, sans-serif"),
        ),

        yaxis=dict(
            title=dict(text="Percent of Total (%)", font=dict(color='black', size=18, family="Roboto Medium, sans-serif")),
            range=[0,100],
            tickfont=dict(color='black', size=18, family="Roboto, sans-serif"),
        ),

        paper_bgcolor='#F4F4F4',
        plot_bgcolor='#F4F4F4',

        legend=dict(
            font=dict(size=14, color="black"),
            bgcolor='#ECECEC',
            bordercolor='black',
            x=.99,
            xanchor='right',
            y=.35,
            yanchor='top',
            borderwidth=1,
        )
    )

    # Import Shock shading
    fig.add_shape(
        x0=2000,
        x1=2011,
        y0=0,
        y1=100,
        fillcolor="gray",
        opacity=0.15,
        line_width=0
    )
    fig.add_annotation(
        x=2005.5,
        y=0.02,
        xref="x",
        yref="paper",
        text="Import Shock",
        showarrow=False,
        font=dict(size=14, color='black')
    )


    # scale mfgsh by 100
    df['mfgsh'] = df['mfgsh']*100

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["mfgsh"],
            line=dict(color="#F7A072", width=3),
            mode="lines",
            name="Manufacturing Share"
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["pct_star_midupp"],
            line=dict(color="#445E93", width=3),
            mode="lines",
            name="Non-College Mid/Upper Income Jobs"
        ),
        secondary_y=False
    )

    st.plotly_chart(fig, width='stretch')

county_dual_axis_chart(county_long_df)


