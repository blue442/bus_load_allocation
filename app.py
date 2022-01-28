import streamlit as st
import pandas as pd
import plotly.express as px

import allocation

ny_zone_dict = {'WEST':'A', 
                'GENESE':'B',
                'CENTRL':'C',
                'NORTH':'D',
                'MHK VL':'E',
                'CAPITL':'F',
                'HUD VL':'G',
                'MILLWD':'H',
                'DUNWOD':'I',
                'N.Y.C.':'J',
                'LONGIL':'K'
                }

RGE_load_class_dict = {101: 'Residential',
					   201: 'Small Commercial',
					   301: 'Gen Service - 100kw',
					   302: 'Gen Service - 100kw High Voltage',
					   401: 'Residential TOU',
					   701: 'Gen Service - 12kw',
					   801: 'SC8 - Secondary',
					   802: 'SC8 - Transmission Secondary',
					   803: 'SC8 - Primary',
					   804: 'SC8 - SubTrans: Industrial',
					   805: 'SC8 - SubTrans: Commercial',
					   901: 'TimeOfUse - Small Demand',
					   902: 'TimeOfUse - Small Demand High Voltage',
					   601: 'Area Lighting',
					   602: 'Street Lighting'
					   }

st.set_page_config(layout="wide")
st.title("Allocating zone loads to busses")


# Load profiles
SDH_profiles_df = pd.read_csv('data/RGE_profile_data.csv')
SDH_profiles_df['Load Class Name'] = SDH_profiles_df['load_class'].map(RGE_load_class_dict)

st.header('Load profiles')
st.markdown('This data demonstrates load profiles that describe the proportion of total load distributed to different \
	         load classes for each season x day x hour. This data is provided by Rochester Gas and Electic.')

profile_season = st.selectbox('Season', 
								options = SDH_profiles_df.Season.unique())
profile_day = st.selectbox('Day', 
							 options = SDH_profiles_df.DayType.unique())

current_SDH_profile = SDH_profiles_df[(SDH_profiles_df['Season']==profile_season) & (SDH_profiles_df['DayType']==profile_day)]

profile_fig = px.area(current_SDH_profile, x="hour", y='p_total_load', color='Load Class Name')
profile_fig.update_layout(height=600, width=1200)
st.plotly_chart(profile_fig, use_container_width=False, sharing="streamlit")



# prep zonal load data
zonal_load_df = pd.read_csv('data/zonal_load_data.csv')
zonal_load_df['Eastern Date Hour'] = pd.to_datetime(zonal_load_df['Eastern Date Hour'])

st.header('Zone Loads')
st.markdown('This is zone-specific load data for New York state broken down by zone, date, and hour')

# choose table options
# zone_list = st.multiselect('Zones of interest', 
# 						   options = ny_zone_dict.keys(),
# 						   default = ny_zone_dict.keys())

zone_date = st.date_input('Date of interest',
						  value = min(zonal_load_df['Eastern Date Hour']),
						  min_value = min(zonal_load_df['Eastern Date Hour']),
						  max_value = max(zonal_load_df['Eastern Date Hour']))

st.write(f'DEBUG: zone_date = {zone_date}')

current_zone_data = zonal_load_df[zonal_load_df['Eastern Date Hour'].isin(pd.date_range(zone_date, periods=24, freq="H"))]

zone_load_fig = px.line(current_zone_data,
	                    x = 'Eastern Date Hour',
	                    y = 'DAM Forecast Load',
	                    color = 'Zone Name')

zone_load_fig.update_layout(height=600, width=1200)
st.plotly_chart(zone_load_fig, use_container_width=False, sharing="streamlit")

# file upload widget
st.file_uploader('load class distribution data', type='.csv')