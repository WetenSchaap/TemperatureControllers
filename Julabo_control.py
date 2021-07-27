# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 15:17:16 2017

@author: Piet Swinkels

This is an example on how to use classywaterbaths.py to control a waterbath - in this case the Julabo.
Much more is possible, just look at the code for guide, it is not particullarily unclear. I hope.
"""

from classywaterbaths import *
import time
import serial
#%% Check which connections are available:

find_available_comports(helpme=True)    # Will return list of usable ports. Change helpme to False if you know how this works

#%% Connect

ju = julabo('com4')		# Fill in port selected with find_available_comports

#%% Start the machine 
 
ju.start_pump()

#%% Set continuous temperature

temp = 31.3				 # max 2 decimals accepted, rest will be rounded
ju.changet(temp)

#%% Set tempramp

Tinit = 31.30       	 	# Typical value: 31.8
Tend = 31.80         	 	# Typical value: 33.25
dT = 0.05            	 	# Typical value: 00.01, temperature steps.
totaltime = 9000     	 	# In seconds, typically domething like 7200 sec (3600 sec = 1 hour)

ju.ramp(Tinit,Tend,dT,totaltime)

#%% Do other random other stuff
 
# This makes it jump between two temperatures every hour until you manually stop the script using ctrl+c.
while True:
	ju.changet(30)
	time.sleep(60*60*1)
	ju.changet(32.5)
	time.sleep(60*60*1)