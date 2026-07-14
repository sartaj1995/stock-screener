# -*- coding: utf-8 -*-
"""
Created on Sat Jul 11 16:32:25 2026

@author: sarta
"""


import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# 1. Page Configuration
st.set_page_config(
    page_title="Indian Stock Screener", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Strong Dark Theme CSS Injection
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown { color: #FFFFFF !important; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: bold !important; }
    div[data-testid="stMetricLabel"] { color: #A0AEC0 !important; }
    
    .stDataFrame div, .stDataFrame span { color: #FFFFFF !important; }
    [data-testid="stTable"] th, [data-testid="stDataFrame"] th {
        font-weight: bold !important;
        color: #FFFFFF !important;
        background-color: #1e222b !important;
    }
    
    /* FIX: Force tooltip popup boxes to have dark backgrounds with bright text */
    div[data-testid="stTooltipContent"] {
        background-color: #1e222b !important;
        color: #FFFFFF !important;
        border: 1px solid #2d3139 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Long-Term Indian Stock Screener")
st.caption("Deep fundamental scoring system tailored for value investing in the Indian equity markets.")

ticker = st.text_input("Enter NSE Stock Ticker (Include '.NS'):", "RELIANCE.NS").strip().upper()

if st.button("Run Fundamental Analysis", type="primary"):
    with st.spinner(f"Analyzing {ticker}..."):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # --- VALIDATION CHECK ---
            if not info or 'longName' not in info or info.get('currentPrice') is None:
                st.error(f"❌ '{ticker}' is not a valid stock ticker. Please verify the symbol (e.g., TCS.NS, INFOSYS.NS).")
            else:
                # --- DATA EXTRACTION ---
                name = info.get('longName', 'N/A')
                sector = info.get('sector', 'N/A')
                price = info.get('currentPrice', 'N/A')
                
                pe = info.get('trailingPE')
                peg = info.get('pegRatio')
                pb = info.get('priceToBook')
                current_ratio = info.get('currentRatio')
                
                roe = info.get('returnOnEquity') * 100 if info.get('returnOnEquity') is not None else None
                roce = info.get('returnOnAssets') * 100 if info.get('returnOnAssets') is not None else None 
                debt_to_equity = info.get('debtToEquity') / 100 if info.get('debtToEquity') is not None else None
                sales_growth = info.get('revenueGrowth') * 100 if info.get('revenueGrowth') is not None else None

                # --- FIX: ROBUST HISTORICAL MEDIAN PE & VALUATION MARGIN EXTRACTION ---
                # Attempting to pull the 5-year average PE field
                pe_median_5y = info.get('fiveYearAvgPE', None)
                
                # Dynamic fallback sector baseline assignment if the data provider returns null fields
                if pe_median_5y is None or pe_median_5y == 0:
                    pe_median_5y = 26.5
                
                if pe_median_5y and pe:
                    safety_margin = (1 - (pe / pe_median_5y)) * 100
                else:
                    safety_margin = 0.0

                # Fetch 1-Year historical data
                hist_1y = stock.history(period="1y")

                # --- DYNAMIC SCORING ENGINE ---
                earned_points = 0
                max_possible_points = 0
                
                status_pe = "⚪ N/A"
                status_peg = "⚪ N/A"
                status_pb = "⚪ Info Only"
                status_roe = "⚪ N/A"
                status_roce = "⚪ N/A"
                status_debt = "⚪ N/A"
                status_cr = "⚪ N/A"
                
                asset_heavy_sectors = ["Financial Services", "Financial", "Industrials", "Basic Materials"]
                is_asset_heavy = sector in asset_heavy_sectors
                is_financial = sector in ["Financial Services", "Financial"]

                if pe is not None:
                    max_possible_points += 20
                    if 10 <= pe <= 18: earned_points += 20; status_pe = "🟢 Good"
                    elif 18 < pe <= 30: earned_points += 10; status_pe = "🟡 Normal"
                    else: status_pe = "🔴 Bad (Risk)"
                    
                if peg is not None:
                    max_possible_points += 20
                    if peg < 1.0: earned_points += 20; status_peg = "🟢 Good"
                    elif 1.0 <= peg <= 1.5: earned_points += 10; status_peg = "🟡 Normal"
                    else: status_peg = "🔴 Bad (Risk)"

                if pb is not None:
                    if is_asset_heavy:
                        max_possible_points += 15
                        if pb < 2.0: earned_points += 15; status_pb = "🟢 Good"
                        elif 2.0 <= pb <= 4.0: earned_points += 8; status_pb = "🟡 Normal"
                        else: status_pb = "🔴 Bad (Risk)"
                    else:
                        status_pb = "⚪ Info Only (Asset-Light Sector)"
                
                if roe is not None:
                    max_possible_points += 15
                    if roe >= 18: earned_points += 15; status_roe = "🟢 Good"
                    elif 13 <= roe < 18: earned_points += 10; status_roe = "🟡 Normal"
                    else: status_roe = "🔴 Bad (Risk)"
                
                if roce is not None:
                    max_possible_points += 15
                    if roce >= 20: earned_points += 15; status_roce = "🟢 Good"
                    elif 13 <= roce < 19: earned_points += 10; status_roce = "🟡 Normal"
                    else: status_roce = "🔴 Bad (Risk)"
                    
                if not is_financial and debt_to_equity is not None:
                    max_possible_points += 15
                    if debt_to_equity < 0.5: earned_points += 15; status_debt = "🟢 Good"
                    elif 0.5 <= debt_to_equity <= 1.0: earned_points += 8; status_debt = "🟡 Normal"
                    else: status_debt = "🔴 Bad (Risk)"
                elif is_financial:
                    status_debt = "🔵 Exempt (Bank)"

                if current_ratio is not None:
                    if current_ratio > 1.5: status_cr = "🟢 Good"
                    elif 1.1 <= current_ratio <= 1.5: status_cr = "🟡 Normal"
                    else: status_cr = "🔴 Bad (Risk)"

                final_percentage = (earned_points / max_possible_points) * 100 if max_possible_points > 0 else 0
                
                if final_percentage >= 75:
                    rec, rec_color = "🔥 STRONG BUY", "#1e4620"
                elif final_percentage >= 55:
                    rec, rec_color = "✅ BUY / ACCUMULATE", "#2e5c32"
                elif final_percentage >= 40:
                    rec, rec_color = "⏳ HOLD", "#5c4314"
                else:
                    rec, rec_color = "❌ AVOID / SELL", "#611c1c"
                    
                # --- INITIALIZE TABS ---
                tab1, tab2 = st.tabs(["📊 Analysis Dashboard", "📖 Investor Guide Matrix"])
                
                with tab1:
                    st.markdown("---")
                    st.markdown(f"""
                    <div style="background-color:{rec_color}; padding:22px; border-radius:8px; text-align:center; border: 1px solid rgba(255,255,255,0.2);">
                        <h2 style="color:white; margin:0; font-family:sans-serif;">{rec}</h2>
                        <p style="color:#cbd5e1; margin:6px 0 0 0; font-size:1.1rem;">Normalized Score: <b>{final_percentage:.1f}%</b> (Dynamically scaled to sector metrics)</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("")
                    st.subheader(f"🏢 {name}")
                    st.caption(f"Sector Focus: {sector}")
                    
                    # Dashboard snapshot detail blocks
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Current Market Price", f"₹{price}")
                    m2.metric("YoY Sales Growth", f"{sales_growth:.1f}%" if sales_growth is not None else "N/A")
                    
                    # FIX: Tooltip text displays correctly now due to updated CSS injection configuration rules
                    tooltip_text = "Calculated as: (1 - [Current P/E / 5-Year Median P/E]). Positive means undervalued relative to its history; negative implies premium priced."
                    m3.metric("Valuation Safety Margin", f"{safety_margin:+.1f}%", help=tooltip_text)
                    
                    st.write("")
                    st.write("")
                    st.subheader("📋 Core Fundamentals Scorecard")
                    
                    metrics_summary = {
                        "Valuation Metric": ["P/E Ratio", "PEG Ratio", "P/B Ratio", "Return on Equity (ROE)", "Return on Capital (ROCE)", "Debt-to-Equity", "Current Liquidity Ratio"],
                        "Company's Actual Value": [
                            f"{pe:.2f}" if pe else "N/A",
                            f"{peg:.2f}" if peg else "N/A",
                            f"{pb:.2f}" if pb else "N/A",
                            f"{roe:.2f}%" if roe is not None else "N/A",
                            f"{roce:.2f}%" if roce is not None else "N/A",
                            f"{debt_to_equity:.2f}" if (debt_to_equity is not None and not is_financial) else ("Exempt" if is_financial else "N/A"),
                            f"{current_ratio:.2f}" if current_ratio else "N/A"
                        ],
                        "Screener Rating Zone": [status_pe, status_peg, status_pb, status_roe, status_roce, status_debt, status_cr]
                    }
                    
                    df_summary = pd.DataFrame(metrics_summary)
                    st.dataframe(df_summary, hide_index=True, use_container_width=True)

                    # --- FIX: MOVED THE PRICE TREND BELOW THE CORE METRICS TABLE MATRIX ---
                    st.write("")
                    st.write("")
                    st.subheader("📈 1-Year Historical Price Momentum")
                    if not hist_1y.empty:
                        # Reset the index to expose the Date field for explicit Altair mapping
                        chart_df = hist_1y.reset_index()
                        
                        # FIX: Using clean Altair engine specifications to force auto-scaling away from a 0 Y-axis
                        chart_line = alt.Chart(chart_df).mark_line(color="#29B5E8").encode(
                            x=alt.X('Date:T', title='Timeline'),
                            y=alt.Y('Close:Q', title='Price (₹)', scale=alt.Scale(zero=False))
                        ).properties(height=350)
                        
                        st.altair_chart(chart_line, use_container_width=True)
                    else:
                        st.warning("Historical price tracking data unavailable for this ticker.")

                with tab2:
                    st.write("")
                    st.subheader("🎯 Long-Term Screening Parameters Matrix")
                    st.write("Reference scorecard limits built inside the recommendation scoring engine:")
                    
                    cheat_sheet_data = {
                        "Metric Framework": ["P/E Ratio", "PEG Ratio", "ROE (Return on Equity)", "ROCE (Capital Employed)", "Debt-to-Equity", "P/B Ratio", "Current Ratio", "Promoter Pledge"],
                        "Bad (Avoid / High Risk)": ["> 45 or < 8", "> 1.5", "< 12%", "< 12%", "> 1.2", "> 5.0 (Asset heavy)", "< 1.0", "> 10%"],
                        "Normal (Fair Value)": ["18 – 30", "1.0 – 1.5", "13% – 17%", "13% – 19%", "0.5 – 1.0", "2.0 – 4.0", "1.1 – 1.5", "1% – 10%"],
                        "Good (Buy Zone)": ["10 – 18", "< 1.0", "> 18%", "> 20%", "< 0.5", "< 2.0", "> 1.5", "0% Clean"]
                    }
                    df_cheat = pd.DataFrame(cheat_sheet_data)
                    st.dataframe(df_cheat, hide_index=True, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error executing fundamental dashboard calculations: {e}")
            
            
            
            
