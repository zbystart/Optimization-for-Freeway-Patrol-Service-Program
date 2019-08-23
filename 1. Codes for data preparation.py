import pandas as pd
import numpy as np
import datetime
import geopandas as gpd
import matplotlib.pyplot as plt

# Read data
Event = pd.read_csv('..\\EVENT - Extra Columns Removed.csv')
Location = pd.read_csv('..\\LOCATION - Extra Columns Removed.csv')

# 1. Calculate the incident durations
def Calculate_Inc_Duration (Event_Data):
    Event = Event_Data
    
    Event['Duration'] = pd.to_datetime(Event['EVENT_CLOSED_DATE']) - pd.to_datetime(Event['EVENT_OPEN_DATE'])
    Event['Duration'] = Event['Duration'] / np.timedelta64(1, 'm')   # save in minutes
    
    return Event

# 2. Remove all NA or no-sense rows from Event file
def Event_Rows_Dropping (Event_Data):
    
    Event = Event_Data
    Event_shape1 = Event.shape
    print('The dimension of the original dataset: ', Event_shape1)
        
    Event = Event[Event['EVENT_CODE'] == 'Incident']
    Event = Event[Event['CENTER_NAME'].isin(pd.Series(['SOC', 'AOC South', 'AOC Central', 'TOC7', \
                                                       'TOC3', 'TOC4', 'CHART Support']))]

    Event = Event[(Event['PRIMARY_FLAG'] != 'nan')      \
                  & (Event['OFFLINE_IND'] != 'nan')     \
                  & (Event['EVENT_OPEN_DATE'] != 'nan') \
                  & (Event['EVENT_CLOSED_DATE'] != 'nan')]
      
    Event = Event[(Event['SOURCE_CODE'] != 'nan')                 \
                  & (Event['INCIDENT_CODE'] != 'nan')             \
                  & (Event['PAVEMENT_CONDITION_CODE'] != 'nan')   \
                  & (Event['FALSE_ALARM_IND'] == 0)]
    
    Event = Event[(Event['MAX_LANES_CLOSED'] <= 12) | (Event['MAX_LANES_CLOSED'] >= 0)]
    Event = Event[(Event['Duration'] <= 1440) & (Event['Duration'] >= 1)]
    
    print('The dimension after removing extra rows: ', Event.shape)
    print('The number of deleted rows is: ', Event_shape1[0] - Event.shape[0])
    
    Event_rows_dropped = Event
    return Event_rows_dropped

def Event_Cols_Dropping (Event_rows_dropped):
    
    df = Event_rows_dropped
    
    # Keep only useful columns 
    df = df[['EVENT_ID', 'CENTER_NAME', 'EVENT_CLOSED_DATE', 'EVENT_OPEN_DATE', 'Duration', \
                   'SOURCE_CODE', 'INCIDENT_CODE', 'PAVEMENT_CONDITION_CODE', 'MAX_LANES_CLOSED']]
    
    Event_cols_dropped = df
    return Event_cols_dropped

# 3.  Edit the values of Lat and Lon
def Location_RowsCols_Dropping (Location):
    
    df = Location
    
    # Edit the values of Lat and Lon
    df['Lat'] = df['LATITUDE_UDEG'] / 1000000
    df['Lon'] = df['LONGITUDE_UDEG'] / 1000000
    df = df.drop(['LATITUDE_UDEG', 'LONGITUDE_UDEG'],  axis = 1)
    
    # 'USPS_STATE_CODE' keeps rows only as 'MD', and 'STATE_FULL_NAME' keeps rows only as 'MARYLAND'
    df = df[(df['USPS_STATE_CODE'] == 'MD') & (df['STATE_FULL_NAME'] == 'MARYLAND')]
    
    # Drop 'USPS_STATE_CODE' and 'STATE_FULL_NAME'
    df = df[['EVENT_ID', 'Lat', 'Lon']]
    
    Location_RowsCols_Dropped = df
    return Location_RowsCols_Dropped

#4. Merge the Event and Location files and add useful columns
def Merge_and_AddCols (Event_cols_dropped, Location_RowsCols_Dropped):
    
    df_event = Event_cols_dropped
    df_location = Location_RowsCols_Dropped
    df = pd.merge(df_event, df_location, on = 'EVENT_ID')
    
    # Extract the event open date, weekday, and hour
    df['Open_Date'] = pd.to_datetime(df['EVENT_OPEN_DATE']).dt.date
    df['Open_Hour'] = pd.to_datetime(df['EVENT_OPEN_DATE']).dt.hour

    df['Open_Weekday'] = pd.to_datetime(df['EVENT_OPEN_DATE']).dt.dayofweek  # Monday is 0...
    df['Open_Weekday'] = df['Open_Weekday'] +1                            # Monday is 1...
    
    #df.to_csv('.\\Merged_Edited_Incidents.csv', index=False)
    print('The dimension of data after merging and adding useful columns', df.shape)
    
    Merged_Edited_Incidents = df
    return Merged_Edited_Incidents

'''
Run the functions
'''
Event = Calculate_Inc_Duration (Event)
Event_rows_dropped = Event_Rows_Dropping (Event)
Event_cols_dropped = Event_Cols_Dropping (Event_rows_dropped)
Location_RowsCols_Dropped = Location_RowsCols_Dropping (Location)
Merged_Edited_Incidents = Merge_and_AddCols (Event_cols_dropped, Location_RowsCols_Dropped)


#5. Spatial Selection in ArcGIS

#6. Brief review of the incidents within 10 miles of the freeways
Incidents = gpd.read_file("..\\Incidents_10miles.shp")  

# Renames columns since ArcGIS shrinked those names
Full_Name = list(Merged_Edited_Incidents)
Full_Name.append("geometry") 
Incidents.columns = Full_Name

IncidentType_Count = Incidents.groupby('INCIDENT_CODE')['EVENT_ID'].count().sort_values(ascending = False)

# Plot
ax = IncidentType_Count.plot.bar(figsize=(30,8))

    ## Annotation
for p in ax.patches:
    ax.annotate(str(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.025))
    ax.set_xticklabels(ax.get_xticklabels(), rotation = -25)

Inc_Duration_Summary = Incidents.groupby('INCIDENT_CODE')['Duration'].describe().sort_values('mean')
Inc_Duration_Summary


# Plot 2
ax3 = Inc_Duration_Summary['mean'].round(decimals = 2).plot.bar(figsize=(20,8))
plt.ylabel("Incidents' Mean Durations (in minutes)", fontsize=16)
plt.xlabel('Incident types', fontsize=16)

    ## Annotation
for p in ax3.patches:
    ax3.annotate(str(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.005))
    #ax.set_xticklabels(ax.get_xticklabels(), rotation = 55)


##### Catetorize the above incident types into more general categories
Gen_Code_df = pd.DataFrame({'General_Category': ['Collision', 'Collision', 'Collision', 'Debris in Roadway', 
                                                 'Disabled In Roadway', 'Emergency Roadwork', 
                                                 'Off Road Activity', 'Other No Additional Information', 
                                                 'Police Activity', 'Utility Problem', 
                                                 'Vehicle Fire', 'Weather Closure', 'Weather Closure', 
                                                 'Weather Closure','Weather Closure','Weather Closure'],
                            
                            'INCIDENT_CODE': ['Collision, Property Damage', 'Collision, Personal Injury', 
                                              'Collision, Fatality', 'Debris in Roadway', 
                                              'Disabled In Roadway', 'Emergency Roadwork', 
                                              'Off Road Activity', 'Other No Additional Information', 
                                              'Police Activity', 'Utility Problem', 
                                              'Vehicle Fire', 'Weather Closure, Debris', 'Weather Closure, High Water', 
                                              'Weather Closure', 'Weather Closure, Utility', 
                                              'Weather Closure, Winter Precip.'] 
                           })
Incidents_newCategoryLabel = pd.merge(Incidents, Gen_Code_df, on = 'INCIDENT_CODE')
Incidents_newCategoryLabel = Incidents_newCategoryLabel[['EVENT_ID', 'General_Category', 'Duration']]

Inc_Duration_Summary2 = Incidents_newCategoryLabel.groupby('General_Category')['Duration'].describe().sort_values('mean')
Inc_Duration_Summary2

# Plot 3
ax2 = Inc_Duration_Summary2['mean'].round(decimals = 2).plot.bar(figsize=(20,8))
plt.ylabel("Incidents' Mean Durations (in minutes)", fontsize=16)
plt.xlabel('Incident types', fontsize=16)

    ## Annotation
for p in ax2.patches:
    ax2.annotate(str(p.get_height()), (p.get_x() * 1.03, p.get_height() * 1.02))
    #ax.set_xticklabels(ax.get_xticklabels(), rotation = 55)

# Use the Matplotlib to plot the histogram
import matplotlib.mlab as mlab
from matplotlib.pyplot import figure

x = Incidents_newCategoryLabel[Incidents_newCategoryLabel['General_Category'] == 'Utility Problem']['Duration']
figure(figsize=(15,5))
n, bins, patches = plt.hist(x, 20, facecolor='darkblue', alpha=0.5)

plt.xlabel('Incident Durations (minutes)')
plt.ylabel('Counts')
plt.title('Histogram of the incident ducations')
plt.show()
