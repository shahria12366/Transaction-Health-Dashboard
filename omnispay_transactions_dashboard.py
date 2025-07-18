import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import altair as alt
import plotly.express as px
import datetime
from datetime import timedelta
from datetime import datetime as dt
import random
import time


st.set_page_config(
    page_title="Transactions Health Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded")

st.markdown('Scroll below for failure heatmap and avg latency for each partner')

hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

def generate_transactions(n=1):
    print('inside generate transactions')
    stages = ['initiation', 'processing', 'settled']
    statuses = ['success', 'failure', 'retry', 'delay']
    failure_reasons = ['', 'API', 'network', 'timeout', 'customer']
    partners = ['PartnerA', 'PartnerB', 'PartnerC']

    data = []
    now = dt.now()

    for i in range(n):
        status = random.choice(statuses)
        reason = random.choice(failure_reasons) if status != 'success' else ''

        # Latency based on status
        if status == 'delay':
            latency = random.randint(1200, 2000)
        elif status == 'retry':
            latency = random.randint(800, 1500)
        elif status == 'failure':
            latency = random.randint(500, 1200)
        else:  # success
            latency = random.randint(100, 600)
            
        # Generate a random timestamp within today
        random_minutes = random.randint(0, now.hour * 60 + now.minute)  # up to current time
        timestamp = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=random_minutes)

        # Timestamp spread over last 3 months
#         random_days = random.randint(0, 0)
#         random_minutes = random.randint(0, 1440)
#         timestamp = now - timedelta(days=random_days, minutes=random_minutes)

        txn = {
            'txn_id': f'TX{i+1:05}',
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'stage': random.choice(stages),
            'status': status,
            'failure_reason': reason,
            'partner': random.choice(partners),
            'latency_ms': latency,
            'amount': round(random.uniform(10, 500), 2),
        }
        data.append(txn)

    return pd.DataFrame(data)

def kpi_calc(df):
    total_trans = df['txn_id'].count()
    failed_trans = df['txn_id'][df['status']=='failure'].count()
    return total_trans, failed_trans

def make_heatmap(input_df, input_y, input_x, input_color):
    heatmap = alt.Chart(input_df, title="🔍 Failure Heatmap by Date and Reason").mark_rect().encode(
        y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Date", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', axis=alt.Axis(title="Failure Reason", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'max({input_color}):Q',
                        legend=alt.Legend(title="Failure Count", titleFontSize=14, labelFontSize=12),
                        scale=alt.Scale(scheme='blues')),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
    ).properties(
        width=900,
        #height=400,
        title=alt.TitleParams(
            text="",
            fontSize=20,
            fontWeight="bold",
            anchor="start",
            offset=10
        )
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    )

    return heatmap
    
def main():
    df = pd.read_csv('transactions_last_3_months.csv')
    with st.sidebar:
        st.title('Real-Time Transaction Health Dashboard')

        status_list = list(df['status'].unique())
        status_list.append('All')
        selected_status = st.selectbox('Status', status_list, index=len(status_list)-1)
        if selected_status != 'All':
            df_filtered = df[df['status'] == selected_status]
        else:
            df_filtered = df

        stage_list = list(df_filtered['stage'].unique())
        stage_list.append('All')
        selected_stage = st.selectbox('Stage', stage_list, index=len(stage_list)-1)
        if selected_stage != 'All':
            df_filtered = df_filtered[df_filtered['stage'] == selected_stage]
            
        if len(df_filtered)==0:
            st.markdown('Data not available. Please reset the filters')
            
        st.markdown('Data refreshed less than a minute ago')
        
        with st.expander('About', expanded=True):
            st.write('''
                - :orange[**Data**]: Sample data generated for demo purposes.
                - :orange[**Reliability %**]: ((Total transactions - Failed transactions)/Total transactions)*100
                ''')
        

    total_trans, failed_trans = kpi_calc(df_filtered)
    reliability_val = round(((total_trans-failed_trans)/total_trans)*100,1)
    
    kpi_col = st.columns((0.20, 0.20, 0.20, 0.20,0.20), gap='medium')   
    with kpi_col[0]:
        with st.container(border=True):
            st.metric(label="Total Transactions", value=df_filtered['txn_id'].count())
    with kpi_col[1]:
        with st.container(border=True):
            st.metric(label="Avg Latency (seconds)", value=round((df_filtered['latency_ms'].mean())/1000,1))
    with kpi_col[2]:
        with st.container(border=True):
            st.metric(label="Reliability (%)", value=reliability_val)
            
    col = st.columns((0.7, 0.3), gap='medium')        
    with col[0]:
        with st.container(border=True):
            #df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'], errors='coerce', format='%d/%m/%y')
            df_filtered['date'] = pd.to_datetime(df_filtered['timestamp']).dt.date
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            print(df_filtered.head())
            txn_count_df = df_filtered.groupby('date')['txn_id'].count().reset_index()
            print(txn_count_df)
            st.markdown("#### Transactions Trend")
            fig = px.line(
            txn_count_df,
            x='date',
            y='txn_id',
            line_shape='spline',
            labels={'date': 'Date', 'txn_id': 'Number of Transactions'})
#             title = 'Transactions Trend')
            st.plotly_chart(fig, use_container_width=True)
        with st.container(border=True):
            failure_df = df[df['status']=='failure']
            if selected_stage != 'All':
                failure_df = failure_df[failure_df['stage'] == selected_stage]
            if len(failure_df) != 0:
                failure_date_group = failure_df.groupby(['date','failure_reason'])['txn_id'].count().reset_index()
                cutoff = failure_date_group['date'].max() - timedelta(days=30)
                df_last_30_days = failure_date_group[failure_date_group['date'] >= cutoff]
                df_last_30_days['date'] = pd.to_datetime(df_last_30_days['date']).dt.strftime('%Y-%m-%d')
                st.markdown("#### 30 Day Failure Heatmap")
                heatmap = make_heatmap(df_last_30_days, 'date', 'failure_reason', 'txn_id')
                st.altair_chart(heatmap, use_container_width=True)
    with col[1]:
        with st.container(border=True):
            failure_df = df[df['status']=='failure']
            if selected_stage != 'All':
                failure_df = failure_df[failure_df['stage'] == selected_stage]
            if len(failure_df) != 0:
                failure_group = failure_df.groupby('failure_reason')['txn_id'].count().reset_index()
                failure_group.rename(columns={'txn_id': 'failures'}, inplace=True)
                st.markdown("#### Failure Reasons Distribution")
                fig = px.pie(
                    failure_group,
                    values='failures',
                    names='failure_reason',
                    title='',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_layout(
                legend=dict(
                    orientation='h',  
                    yanchor='top',    
                    y=-0.3,           
                    xanchor='center', 
                    x=0.5             
                ))
                st.plotly_chart(fig, use_container_width=True)
        with st.container(border=True):   
            partner_group = df_filtered.groupby('partner')['latency_ms'].mean().reset_index()
            partner_group.rename(columns={'latency_ms': 'latency'}, inplace=True)
            partner_group['latency'] = round(partner_group['latency']/1000,1)
            st.markdown("#### Avg Latency for Partners")
            fig = px.bar(
                partner_group,
                x='partner',
                y='latency',
                labels={'partner': 'Partner', 'latency': 'Avg Latency (seconds)'},
                title='')
            st.plotly_chart(fig, use_container_width=True)
            
    if "last_run" not in st.session_state:
        st.session_state.last_run = dt.now()
    # Check if 2 hours have passed to update new data
    if dt.now() - st.session_state.last_run >= timedelta(minutes=60):
        df_new = generate_transactions(n=1)
        df = pd.concat([df, df_new], ignore_index=True)
        df.to_csv('transactions_last_3_months.csv')
        st.session_state.last_run = dt.now()       
    time.sleep(60)
    st.rerun()
main()