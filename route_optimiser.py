# -*- coding: utf-8 -*-
"""
@author:    shanemccarthy
Studnet_id: 14200512
Created on Sat Sep 12 11:50:27 2015

Purpose:This program reads in two tables from the ‘renewable.db’ database. The 
        first table ‘location’ contains the latitude, longitude and production 
        for a number of sites. The second table ‘ports’ contains the latitude 
        and longitude for a number of ports. The core function of this program 
        is to optimally select the location of a new centralised production 
        plant to be located at one of the existing sites, along with optimally 
        selecting a port to which the new production plant will export from.
"""

#import libraries
import os 
import sqlite3
import numpy as np
import math

#set woking dir 
os.chdir('/Users/shanemccarthy/Dropbox/Masters/MIS40750/Python/Assignment')

#define data structures
raw_location = []
port_location = []
raw_to_raw = np.empty((10, 10), dtype=object)
raw_to_port = np.empty((10, 3), dtype=object)
site_options = np.empty((10, 7), dtype=object)
selected = np.empty((6), dtype=object)

def DBconnect(DBname):
  """  
  This function queries the input database and selects all columns from the 
  ‘locations’ and ‘ports’ tables reading both into two lists. If database is 
  not found in the working directory an error message is printed. 
  """
  if os.path.isfile(DBname):
    conn = sqlite3.connect(DBname)
    c = conn.cursor()
    
    c.execute("SELECT * FROM location;") 
    for item in c:
        raw_location.append(item)
    c.execute("SELECT * FROM ports;") 
    for item in c: 
        port_location.append(item)     
        
    conn.close()
    return raw_location, port_location
  else:
    # if the database is not in the directory
    path=os.getcwd()
    print "ERROR: The database ""%s"" does not exist in %s." % (DBname ,path)
    

def haversine(lon1, lat1, lon2, lat2):
    """
    This function calculates the distance in km between two sets of 
    latitude/longitude points factoring in the curvature of the earth 
    (not significant for low distance). Function sourced from stackoverflow 
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # radius of earth in kilometers. Use 3956 for miles
    return c * r


def dist_btwn_raw_loc(index):
    """
    This function calculates the distance between all raw material sites 
    returning a 10 x 10 object
    """
    raw_location2 = raw_location[index]
    # use x to increment across the return object
    x = 0
    for data in raw_location:
        raw_to_raw[index][x] = haversine(data[0], data[1], raw_location2[0], 
        raw_location2[1])
        x += 1
    return raw_to_raw
    

def dist_raw_ports(index):
    """
    This function calculates the distance between all raw material sites and 
    all ports returning a 10 x 3 object

    """
    raw_location2 = raw_location[index]
    #u se x to increment across the output object
    x = 0
    for data in port_location:
        raw_to_port[index][x] = haversine(data[0], data[1], raw_location2[0], 
        raw_location2[1])
        x += 1
    return raw_to_port


def optimiser(index):     
    """
    This function solves the optimisation problem. For each site the total 
    transport distance, total transport weight, site weight, total weight, 
    closest port distance, closest port id and weighted transportation distance 
    (which is the selection criteria) is calculated. A summary tables containing 
    all of these inputs for each site is output when the program is called. 
    """
    # initialise all values of the retuned object to zero
    site_options[index,:] = 0 
    
    for i in range(0, len(raw_to_raw[index])):    
        # sum the transport distance for each site
        site_options[index][0] += raw_to_raw[index][i]
        # sum the transport TO weight for each site
        # include the site's own weight in a seperate field 
        if i != index:  
            site_options[index][1] += raw_location[i][2]
        else: site_options[index][2] = raw_location[index][2]       
        # calculate the total weight (transport TO weight + site's own weight)
        site_options[index][3] = site_options[index][2]+site_options[index][1]
        # find the minimum port distance and assign to field
        site_options[index][4] = min(raw_to_port[index][0],
        raw_to_port[index][1],raw_to_port[index][2])
        
    # look up the port ID for the minimum port distance and assigne to field    
    for x in range(0, len(raw_to_port[index])):
        if site_options[index][4] == raw_to_port[index][x]: 
           site_options[index][5] = x
    # calculate the weighted distance for each site as
    # (transport distance to site)*(transport weight to site)  +
    # (transport distance to port)*(transport weight to port)     
    site_options[index][6] = site_options[index][0]*site_options[index][1] 
    + site_options[index][3]*site_options[index][4]
    return site_options 


def reporter():
    """
    This function finds the minimum weighted distance (selection criteria) 
    returning the details of optimum  site and port
    """
    # initialise all values of the retuned object to zero
    selected[:] = 0     
    # find the minimum weighted distance and store value in wd 
    wd  = min(site_options[:,6])
    for i in range(0, len(site_options)):
    # for the minimum weighted distance find corresponding details for site/port
        if wd == site_options[i][6]: 
            selected[0] = i 
            selected[1] =raw_location[i][0]
            selected[2] =raw_location[i][1]
            selected[3] =site_options[i][5]
            selected[4] =port_location[selected[3]][0]
            selected[5] =port_location[selected[3]][1]
            
    return selected


def engine():
    """
    This function loops through dist_btwn_raw_loc(),dist_raw_ports() and 
    optimiser() for each site 
    """
    for index in range(len(raw_location)):
        #print i
        dist_btwn_raw_loc(index)
        dist_raw_ports(index)
        optimiser(index)


def main():
    """
    Main calls all the previous functions, it outputs the optimally selected 
    site and port with their corresponding coordinates. The tables created by 
    the optimiser() function is also converted to a dataframe and printed out.
    """

    DBconnect('renewable.db')
    engine()
    reporter()
    #covert site_options to a dataframe
    site_options_df = pd.DataFrame(site_options, columns=['T_dist_site',
    'T_wght_site','Wght_site','T_wght','Clst_dist_port','Port_id',
    'T_wghtd_dist'])
    site_options_df['Site_id']=site_options_df.index
       
    print ""
    print "The optimum site to build the plant is Site",selected[0],"Latitude:",\
    selected[1],"Longitude:",selected[2]
    print""
    print "From this site the optimum port to transport to is Port",selected[3],\
    "Latitude:",selected[4],"Longitude:",selected[5]
    print""
    print "A summary table containing all key input metrics can be found below:"
    print""
    print""
    print site_options_df

if __name__ == "__main__":
    main()
    

  
  
  
  
































