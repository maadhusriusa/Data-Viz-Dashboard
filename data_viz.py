import streamlit as st
import pandas as pd
import numpy as np
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from PIL import Image
from plotly.subplots import make_subplots

st.set_page_config(page_title="Strategy Fox", page_icon=":fox_face:", layout="wide")
reduce_header_height_style = """
    <style>
        div.block-container {padding-top:0.5rem;}
    </style>
"""

st.markdown(reduce_header_height_style, unsafe_allow_html=True)
authenticator = stauth.Authenticate(
    dict(st.secrets['credentials']),
    st.secrets['cookie']['name'],
    st.secrets['cookie']['key'],
    st.secrets['cookie']['expiry_days'],
    st.secrets['preauthorized'])

col1, col2, col3, col4, col5, col6 = st.columns([0.4,0.1,0.1,0.1,0.1,0.2])
with col1:
    sf_logo = Image.open('sf_logo.png')
    st.image(sf_logo, width=450)
with col6:
    authenticator.logout('Logout', 'main', key='unique_key')

name, authentication_status, username = authenticator.login('Login', 'main')

if st.session_state["authentication_status"]:
    st.title("Strategy Fox: Overview 🎯")
    sidebar = st.sidebar
    expand_data = sidebar.expander("Refresh data")
    one_time_data = expand_data.file_uploader(label="Upload recent data", type="xlsx")
    if one_time_data:
            df = pd.read_excel(one_time_data, sheet_name=None)
            output_file_path = 'CLIENT FINANCIALS.xlsx'
            with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
                # Iterate over each sheet and write it to the new Excel file
                for sheet_name, df in df.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            print("Data successfully written to the new Excel file!")
    one_time_data = pd.read_excel("CLIENT FINANCIALS.xlsx", sheet_name=None)
    master_data = one_time_data['Master Sheet']
    payment_details = one_time_data['Payment Details']
    invoice_details = one_time_data['Invoice Breakup']

    payment_details['Payment Date'] = pd.to_datetime(payment_details['Payment Date'],errors='coerce')
    payment_details['Payment Date'] = payment_details['Payment Date']
    max_date = str(payment_details['Payment Date'].max())
    print(max_date)
    st.markdown("**_Data refreshed as of: {0}_**".format(max_date))

    #get the latest data of refresh
    payment_details['Payment Date'] = pd.to_datetime(payment_details['Payment Date'])
    latest_entry = payment_details['Payment Date'].max()
    print("lastest",latest_entry)

    #Important KPIs

    no_clients = master_data["Client ID"].count()
    no_active_clients = master_data["Client ID"].count()
    total_invoice = round(invoice_details["Amount"].sum(),0)
    tds  = round(invoice_details["TDS Amt"].sum(),0)
    never = round(invoice_details["Never"].sum(),0)
    Amt_to_received  = total_invoice - tds - never

    OOPE = round(invoice_details["OOPE"].sum(),0)
    Refund = round(invoice_details["Refund"].sum(),0)
    Profit_recvd = round(invoice_details["Received"].sum(),0) - OOPE - Refund
    pending_amt = Amt_to_received - round(invoice_details["Received"].sum(),0)

    #Heading
    st.markdown("#### KPIs ")

    # write metrics as KPIs on the dashboard
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Clients#", master_data["Client ID"].nunique())
    col2.metric("Total Invoice", "₹{:,.1f} L".format(total_invoice/100000))
    col3.metric("TDS Amount", "₹{:,.1f} K".format(tds/1000))
    col4.metric("Loss", "₹{:,.1f} K".format(never/1000))
    col5.metric("Amount to be received", "₹{:,.1f} L".format(Amt_to_received/100000))

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Active Clients#", master_data["Client ID"].nunique())
    col2.metric("OOPE", "₹{:,.1f} K".format(OOPE/1000))
    col3.metric("Refund Amount", "₹{:,.1f} K".format(Refund/1000))
    col4.metric("Profit", "₹{:,.1f} L".format(Profit_recvd/100000))
    col5.metric("Pending Amount", "₹{:,.1f} L".format(pending_amt/100000))

    st.divider()

    df = invoice_details[['Client Name', 'Amount', 'Pending']]
    #print(df.head(5))

    df_grouped = df.groupby('Client Name').agg(Total_invoice_amt=('Amount', 'sum'),
                                            amt_pending=('Pending', 'sum')).reset_index()
    df_grouped['Amount_received'] = df_grouped['Total_invoice_amt'] - df_grouped['amt_pending']
    print(df_grouped.head())

    #1st bar chart 

    # Top 10 clients by total invoice

    top_10_df = df_grouped.nlargest(10, 'Total_invoice_amt')
    print("Top 10 clients")
    print(top_10_df)

    fig1 = px.bar(top_10_df, x='Client Name', y='Total_invoice_amt', 
                title='Top 10 clients by total invoice',
                text= top_10_df['Total_invoice_amt']/1000,
                color='Total_invoice_amt')

    fig1.update_traces(
        marker_line_width = 0, 
        texttemplate='%{text:.1f} K',  # Format text (convert to scientific notation, then append 'L' for lakhs)
        textposition='auto',
        hovertemplate = '%{x}: %{text:.1f} K'
    ) 

    fig1.update_layout(
        xaxis_title="Client Name",
        yaxis_title="Total Invoice Amount (₹)",
        title_font_size=20
    )
    st.plotly_chart(fig1, height = 300, use_container_width = True)

    #2nd bar chart 

    # Amount pending by clients
    df_pending = df_grouped[df_grouped['amt_pending'] > 0]
    df_pending = df_pending.sort_values(by=['amt_pending'], ascending=False)
    print(df_pending.head())

    fig2 = go.Figure()

    # Adding the first bar (Column1_sum)
    fig2.add_trace(go.Bar(
        x=df_pending['Client Name'],
        y=df_pending['Amount_received'],
        name='Amount received',
        text= df_pending['Amount_received']/1000
    ))

    # Adding the second bar (Column2_sum)
    fig2.add_trace(go.Bar(
        x=df_pending['Client Name'],
        y=df_pending['amt_pending'],
        name='Amount Pending',
        text= df_pending['amt_pending']/1000
        ))

    # Setting the layout to 'stack' the bars
    fig2 = fig2.update_layout(barmode='stack', 
                            title="Amount received and pending by client",
                            title_font_size=20,
                            xaxis_title="Client Name", yaxis_title="Amount"
                            )

    fig2.update_traces(
        marker_line_width = 0, 
        texttemplate='%{text:.1f} K',  # Format text (convert to scientific notation, then append 'L' for lakhs)
        textposition='auto',
        hovertemplate = '%{x}: %{text:.1f} K'
    ) 

    # Displaying the figure
    st.plotly_chart(fig2, height = 300, use_container_width = False)

    #3rd bar chart 

    # Total revenue by month and total customers onboarded

    master_data['Client Onboarded Date'] = pd.to_datetime(master_data['Client Onboarded Date'])
    invoice_details['Invoice Date'] = pd.to_datetime(invoice_details['Invoice Date'])
    #Fetching range of months
    min_date = master_data['Client Onboarded Date'].min()
    max_date = invoice_details['Invoice Date'].max()
    month_range = pd.date_range(start=min_date, end=max_date, freq='MS')
    df_months = pd.DataFrame(month_range, columns=['Month'])
    df_months['Year'] = df_months['Month'].dt.year
    df_months['Month_Num'] = df_months['Month'].dt.month
    df_months['Month_Abbr'] = df_months['Month'].dt.strftime('%b-%Y')
    df_months['mon_year'] = (df_months['Year'] * 100) + df_months['Month_Num']

    #calculating number of clients onboarded per month
    df1 = master_data[['Client ID', 'Client Onboarded Date']]
    df1 = df1.dropna()
    df1['mon_year'] = round((df1['Client Onboarded Date'].dt.year * 100) + df1['Client Onboarded Date'].dt.month,2).astype(int)
    df1_grouped = df1.groupby('mon_year').agg(no_clients_onboarded = ('Client ID', 'count')).reset_index()

    #calculating total billings per month

    df2 = invoice_details[['Client Name', 'Invoice Date','Amount']]
    df2 = df2.dropna()
    df2['mon_year'] = round((df2['Invoice Date'].dt.year * 100) + df2['Invoice Date'].dt.month,2).astype(int)
    df2_grouped = df2.groupby('mon_year').agg(total_billing = ('Amount', 'sum')).reset_index()

    #creating the final dataframe

    month_df = pd.merge(df_months,df1_grouped,how = 'left', on = 'mon_year')
    fin_df = pd.merge(month_df, df2_grouped, how = 'left', on = 'mon_year').fillna(0)
    fin_df['Year'] = fin_df['Year'].astype(str)

    col1, col2 = st.columns(2)
    with col1:
        year = st.multiselect("Select Year", options=fin_df["Year"].unique())

    if year:
            fin_df = fin_df[fin_df["Year"].isin(year)]

    #Graph
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bar chart for total revenue
    fig3.add_trace(
        go.Bar(x=fin_df['Month_Abbr'], y=fin_df['total_billing'], name='Total Billing'),
        secondary_y=False
    )

    # Add line chart for number of clients
    fig3.add_trace(
        go.Scatter(x=fin_df['Month_Abbr'], y=fin_df['no_clients_onboarded'], mode='lines+markers', name='#Clients Onboarded'),
        secondary_y=True
    )

    # Update layout
    fig3.update_layout(
        title='Total Billings and Number of clients onboarded per month',
        title_font_size=20,
        xaxis_title='Month-Year',
        yaxis_title='Total Billing',
        yaxis2_title='No of Clients Onboarded',
        xaxis=dict(tickangle=-45)  # Rotate x-axis labels if needed
    )
    st.plotly_chart(fig3, height = 300, use_container_width = False)

    #st.dataframe(payment_details)
elif st.session_state["authentication_status"] == False:
    # st.title("Login")
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')


