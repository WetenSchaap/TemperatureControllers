# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 15:17:16 2017

@author: Piet Swinkels

This is an example on how to use classywaterbaths.py to control a waterbath - in this case the Julabo.
Much more is possible, just look at the code for guide, it is not particullarily unclear.
"""

from classywaterbaths import *
import time
import serial

#%% Connect

ju = julabo('com4')		# Check the com# in "Device Manager" run-->devmgmt.msc)

#%% Start the machine 
# This is not needed in HaakeF6, which starts its pump automatically
 
ju.start()

#%% Set continuous temperature

temp = 31.3				 # max 2 decimals accepted
ju.changet(temp)

#%% Set tempramp

Tinit = 31.30       	 	# Typical value: 31.8
Tend = 31.80         	 	# Typical value: 33.25
dT = 0.05            	 	# Typical value: 00.05, temperature steps.
totaltime = 9000     	 	# In seconds, typically 7200 sec (3600 sec = 1 hour)

ju.ramp(Tinit,Tend,dT,totaltime)

#%% Do other random other stuff
 
# This makes it jump between two temperatures every hour until you manually stop the programm.
while True:
	ju.changet(30)
	time.sleep(60*60*1)
	ju.changet(32.5)
	time.sleep(60*60*1)