import streamlit as st
from pathlib import Path
import json, pandas as pd

DB=Path('trendpulse_data.json')
def load():
    return json.loads(DB.read_text()) if DB.exists() else {'drafts':[],'topics':[],'metrics':[]}
def save(d): DB.write_text(json.dumps(d,indent=2),encoding='utf-8')
data=load()
if not data['drafts']:
    data['drafts']=[{'id':1,'title':'Example TrendPulse Daily draft','niche':'Trending topics','status':'Awaiting approval','scheduled_for':'20:00 SAST','copyright_check':'Pending','script':'Placeholder draft. Live trend research and rendering will be added in the next build.'}]
    save(data)
st.set_page_config(page_title='TrendPulse Daily',layout='wide')
st.title('TrendPulse Daily')
st.caption('Automated content control • 08:00 SAST review • Human approval required')
a,b,c,d=st.tabs(['Approval Queue','Trends','Analytics','Settings'])
with a:
    st.header('Daily approval queue')
    st.info('Drafts are intended to be ready by 08:00 SAST. Nothing publishes without approval.')
    for x in data['drafts']:
        with st.container(border=True):
            st.subheader(x['title'])
            st.write('Niche:',x['niche'])
            st.write('Status:',x['status'])
            st.write('Scheduled time:',x['scheduled_for'])
            st.write('Copyright check:',x['copyright_check'])
            st.text_area('Script preview',x['script'],key=f"s{x['id']}")
            c1,c2=st.columns(2)
            if c1.button('APPROVE & SCHEDULE',key=f"a{x['id']}"):
                x['status']='Approved — awaiting YouTube integration'
                save(data); st.success('Approval recorded locally.'); st.rerun()
            if c2.button('REJECT',key=f"r{x['id']}"):
                x['status']='Rejected — needs revision'
                save(data); st.warning('Draft rejected.'); st.rerun()
with b:
    st.header('Trending topics')
    st.info('Live trend provider will be connected in the next development stage.')
    st.dataframe(pd.DataFrame(data['topics']) if data['topics'] else pd.DataFrame(columns=['Topic','Niche','Interest','Competition']))
with c:
    st.header('Analytics')
    st.info('YouTube Analytics connection will populate views, watch time, retention and revenue when available.')
    st.dataframe(pd.DataFrame(data['metrics']) if data['metrics'] else pd.DataFrame(columns=['Video','Views','Watch time','Revenue']))
with d:
    st.header('Settings')
    st.write('Approval deadline: 08:00 SAST')
    st.write('Default publishing time: 20:00 SAST')
    st.write('Publishing mode: Manual approval required')
    st.write('Channel: TrendPulse Daily')
