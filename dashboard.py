import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import plotly.express as px

# ---------------------------
# GEMINI SETUP
# ---------------------------
genai.configure(api_key="")  # Replace with your key
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------------------
# PARAMETERS
# ---------------------------
available_params = [
    "Company_Name", "Location", "Industry_Type", "Sub_Industry",
    "Company_Revenue_USD_Billions", "Market_Cap_USD_Billions",
    "Employee_Count", "Founded_Year", "Revenue_Growth_Rate_Percent",
    "Profit_Margin_Percent", "ROE_Percent", "Debt_to_Equity_Ratio",
    "R&D_Spending_Percent_of_Revenue", "Global_Presence_Countries",
    "Stock_Exchange"
]

# ---------------------------
# STREAMLIT CONFIG
# ---------------------------
st.set_page_config(page_title="Company Competitive Benchmarking Dashboard", layout="wide")
st.title("Company Competitive Benchmarking Dashboard")

with st.sidebar:
    st.header("User Inputs")
    company_name = st.text_input("Enter company name to benchmark")
    num_competitors = st.slider("Number of competitors", 1, 15, 5)
    selected_params = st.multiselect(
        "Select parameters to prioritize", available_params, default=available_params
    )
    run_analysis = st.button("Run Benchmark")

# ---------------------------
# GEMINI FUNCTIONS
# ---------------------------
def get_benchmark_data(company, competitors):
    prompt = f"""
You are a competitive benchmarking expert.

Generate a table comparing {company} and its top {competitors} competitors.

Rules:
1. Include the company itself and exactly {competitors} competitors.
2. Use these exact column names and in this order:
{", ".join(available_params)}
3. Each row must have values for ALL columns. If unknown, write "N/A".
4. All rows must have the same number of values matching the headers exactly.
5. Return ONLY CSV text. No extra commentary, no markdown, no explanations.
6. The first row MUST be the column headers exactly as given.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def get_company_info(company):
    prompt = f"""
Provide a short, clear summary about {company}, including:
- Industry and main products/services
- Headquarters location
- Founding year
- Any notable facts or achievements
Keep it under 80 words.
"""
    try:
        res = model.generate_content(prompt)
        return res.text.strip()
    except:
        return "Could not fetch company info."

def get_companies_info(df):
    info_dict = {}
    for comp in df["Company_Name"]:
        info_dict[comp] = get_company_info(comp)
    return info_dict

def get_table_insights(df):
    prompt = f"""
You are a business analyst. Analyze the following company benchmarking table
and provide key insights, trends, and learnings based ONLY on this table.

Data:
{df.to_csv(index=False)}

Guidelines:
- Mention notable leaders in different metrics.
- Highlight any unusual or interesting patterns.
- Keep it concise but insightful.
- Do not mention companies not in this table.
"""
    try:
        res = model.generate_content(prompt)
        return res.text.strip()
    except:
        return "Could not generate insights."

# ---------------------------
# CSV to DataFrame
# ---------------------------
def parse_csv_to_df(csv_text):
    try:
        df = pd.read_csv(io.StringIO(csv_text))
        return df
    except Exception as e:
        st.error(f"Could not parse CSV from Gemini: {e}")
        return None

# ---------------------------
# MAIN LOGIC
# ---------------------------
df_result = None

if run_analysis:
    if not company_name:
        st.error("Please enter a company name before running.")
    else:
        with st.spinner("Fetching data from Gemini..."):
            csv_text = get_benchmark_data(company_name, num_competitors)
            df_result = parse_csv_to_df(csv_text)

        if df_result is not None and not df_result.empty:
            # Filter for selected params
            df_result = df_result[[col for col in selected_params if col in df_result.columns]]

            # Create Tabs
            tab1, tab2, tab3, tab4 = st.tabs(["Benchmark Table", "Analysis", "Company Info", "Insights"])

            # ---------------------------
            # TAB 1: Benchmark Table
            # ---------------------------
            with tab1:
                st.subheader("Benchmark Table")
                st.dataframe(df_result, use_container_width=True)
                # CSV Download Button
                st.download_button(
                    label="Download CSV",
                    data=df_result.to_csv(index=False),
                    file_name="benchmark.csv",
                    mime="text/csv"
                )

            # ---------------------------
            # TAB 2: Analysis
            # ---------------------------
            with tab2:
                st.subheader("Summary Insights from Analysis")
                numeric_cols = df_result.select_dtypes(include=['number']).columns
                for col in numeric_cols:
                    if df_result[col].notna().any():
                        top_row = df_result.loc[df_result[col].idxmax()]
                        st.write(f"Highest {col}: {top_row['Company_Name']} ({top_row[col]})")

                st.subheader("Visual Analysis")
                for col in numeric_cols:
                    fig = px.bar(df_result, x="Company_Name", y=col, title=f"{col} Comparison")
                    st.plotly_chart(fig, use_container_width=True)

            # ---------------------------
            # TAB 3: Company Info
            # ---------------------------
            with tab3:
                st.subheader("Brief Info for All Companies in Table")
                with st.spinner("Fetching company info..."):
                    all_info = get_companies_info(df_result)
                for comp, info in all_info.items():
                    with st.expander(comp):
                        st.write(info)

            # ---------------------------
            # TAB 4: Insights
            # ---------------------------
            with tab4:
                st.subheader("Insights and Learnings from the Table")
                with st.spinner("Generating insights..."):
                    insights = get_table_insights(df_result)
                st.write(insights)

        else:
            st.error("No valid data returned by Gemini.")
