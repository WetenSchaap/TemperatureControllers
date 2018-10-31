import serial
import time
import warnings
import math
import sys

'''
@author: Piet Swinkels
Based on simonexp.py, written by Simon Stuij. I just put everything from simonexp.py in classes so that we can control two systems simultaniously. I also added support for haakeF6 and haakePhoenix, and made everything a bit more uniform.

All these classes are used in a very similar way. First, we assign the class of the 
machine we want to use to a variable with the corect comport (see devices and printers). 
We can then set the temperature using self.changet(temp), and ramp the temperature
using self.ramp(Tinit,Tend,dT,totaltime). Note that all machines/classes are harmonized as much as possible,
but it's not perfect. Read it for a minute, or at least ask someone about it. Please.

Guide for adding new machines:
	* Every class should *at least* contain a function:
			- _readtemp_set (okay, not really, but is really really usefull to have!)
			- _set_temperature
			These functions should contain a call to _in_command and _out command respectively, with the command found in the manual.
	* Let the class inherit from the superclass Temperature_controller, or, if we allready have a controller from the brand, the brand Superclass (i.e. 'haake').
	* Stuff should now work automatically

To be fixed/implemented:
	* At PC of fast&slow confocal, Julabo has the tendency to lose connection with PC if we don't invoke it often enough. This leads to a restart to restore connection. This is probably due to a bad cable or something, not this script.

	* Introduce some variable that stores the temperature at different moments in time?
		--> Use 'real' temperature vs. just storing temperature if we set it to something different.
'''


if 'win' in sys.platform:
	try:
		wv = sys.getwindowsversion()
		if wv.major <= 5: # If using windows 5 (WINDOWS XP) or below, give a warning
			print("*****I SMELL WINDOWS XP*****")
			warnings.warn("The serial ports have the tendency to loose connection when connected for extended periods of time without commands comming in. Therefore, I advise using the 'wiggle' function as an alternative to 'changet'. This wiggles the temperature by 0.01 degrees every 2 minutes. This way, connection will not be lost and you will be safe!")
			print("*****I STILL SMELL WINDOWS XP*****")
	except:
		pass


class Temperature_controller():
	'''
	This is the superclass. It cannot be used directly, but all temperature controllers inherit from it. 
	So, basically, if you change something here, it will change something in all classes. Usefull for things that all classes do, so for instance the ramping function.
	This Class has great power, use with great responsibility.
	'''
	def __init__(self,comport):
		self.comport = comport
	
	def __repr__(self):
		message = " <%s object controlling comport %s>" % (str(self.__class__),self.comport)
		return message 
	
	def __str__(self):
		message = "Connection to Haake F6 at comport:\t%s\nInternal temperature is currently:\t%.2f\nSet temperature is currently:\t%.2f\n" % (self.comport,self._readtemp_internal(),self._readtemp_set())
		return message
	
	def _initialize_connection (self,baudrate,bytesize,parity,stopbits,timeout=None,xonxoff=False,rtscts=False,write_timeout=None,dsrdtr=False,inter_byte_timeout=None):
		try: 
			return serial.Serial(self.comport,baudrate=4800,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=5,xonxoff=False,rtscts=False,write_timeout=5,dsrdtr=False,inter_byte_timeout=None)
		except serial.SerialException:
			raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc)')
		
	def closecom(self):
		'''
		Close port if comport is open.
		'''
		if self.com.isOpen(): 
			self.com.close()
			
	def opencom(self):
		'''
		Open port if comport is closed.
		'''
		if not self.com.isOpen():
			self.com.open()
		
	def _out_command(self,command):
		'''
		Setting temperature values of parameters. Does not return anything.
		'''
		#self.opencom()
		self.com.write( command.encode() )
		self._flush()
		#self.closecom()
		
	def _in_command(self,command):
		'''
		Asking for parameters or temperatures to be returned. Returns raw message.
		'''
		#self.opencom()
		self.com.write( command.encode() )
		time.sleep(0.1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		self._flush()
		#self.closecom()
		return message
	
	def _flush(self):
		'''
		Flush the connection.
		'''
		self.com.flushInput()
		self.com.flushOutput()
		
	def _readtemp_internal(self):
		'''
		This function is made to be overridden in one of the child classes. Just to avoid errors in printing incomplete classes!
		'''
		return 0
	
	def _readtemp_set(self):
		'''
		This function is made to be overridden in one of the child classes. Just to avoid errors in printing incomplete classes!
		'''
		return 0
		
	def ramp(self,Tinit,Tend,dT,totaltime,ask,verbose=False):
		'''
		Makes a block temperature ramp with device for controlling temperature.

		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Temperature step of ramp in deg C.
			* totaltime : Total time of measurement in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* self      : The object used to control temperature device.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		
		t00 = time.clock() 	 	 	 	 	 	 	 	 	# Initialize internal clock (in seconds)
		steps = round((Tend-Tinit)/dT)	 	 		 	 	 	# Number of steps
		Trange = [round(Tinit + i*dT,2) for i in range(0,steps+1)] # Temperatures we will visit
		
		print('Temperature range is given by:\n'+str(Trange))
		
		waittime = totaltime / len(Trange) 						# Waiting time between steps in sec
		waittimemin = waittime / 60 	 	 		 		 	# Waiting time between steps in min
		waittimeh = waittimemin / 60 							# Waiting time between steps in hours
		totaltimeh = totaltime / 60 / 60						# Total time in hours
		
		
		print('The waiting time between each step is %.2f minutes / %.2f hours.' % (waittimemin,waittimeh))
		print('The total time of this ramp is %.2f hours.' % (totaltimeh,))
		
		if ask:
			test = input("Press enter to start ramp, press q to abort.")
			if 'q' in test:
				raise ValueError("Aborted measurement before start.")
				
		t0=time.clock()
		
		print('Starting at internal clock time: %i sec.' % (int(round(t0))))
		
		for T in Trange:
			tnew = time.clock()
			print('Changing temperature to %.2f deg C at internal time: %.2f sec.' % (T,tnew))
			pasttime = int(round(tnew-t0))/60
			print('Time past since last temperature change: %.2f minutes.' % (pasttime,) )
			#print('difference in time before last change not rounded '+str(tnew-t0))
			t0 = tnew		
			
			self.changet(T)
			
			tafterchange = time.clock()
			tcorrection = tafterchange-t0
			if verbose:
				print('time it took to change sp '+str(round(tafterchange-t0)))
				print('time it took to change sp not trounded '+str(tafterchange-t0))
			
			# This weird thing makes it possible to interrupt sleeping
			slptime = math.floor(waittime-tcorrection)
			for i in range(slptime):
				time.sleep(1)
			time.sleep(waittime-tcorrection-slptime)
			
		print('Total time of the measurement: %.2f minutes / %.2f hours.' % ((time.clock()-t00) / 60 , (time.clock()-t00) /60/60) )
	
	        
	def ramp_steptime(self,Tinit,Tend,dT,steptime,ask,verbose=False):
		'''
		Equivalent to ramp(), but uses steptime instead of totaltime	
		Makes a block temperature ramp with device for controlling temperature.

		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Tempearture step of ramp in deg C.
			* steptime  : Total time of a step in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* self      : The object used to control temperature device.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		steps = round((Tend-Tinit)/dT)	 	 		 	 	 	# Number of steps
		Trange = [round(Tinit + i*dT,2) for i in range(0,steps+1)] # Temperatures we will visit
		totaltime = len(Trange) * steptime
		self._ramp(Tinit,Tend,dT,totaltime,ask,verbose)
	
	def ramp_smooth(self,Tinit,Tend,totaltime,ask,verbose):
		'''
		Equivalent to ramp(), but with dT = 0.01 preset.
		Makes a continues temperature ramp (or as close to it as we can with our setup) with device for controlling temperature.

		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* totaltime : Total time of the experiment in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* self      : The object used to control temperature device.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		dT = 0.01
		self._ramp(Tinit,Tend,dT,totaltime,ask,verbose)
		
	def changet(self,temp):
		"""
		Changes temperature of temperature control unit to temp, and checks if it was succesfull.
		Number will be rounded to 2 decimals.
		"""
		temp = round(temp,2) 	# In case somebody still puts in ##.###, note that ##.# or ## is no problem
		self.opencom()
		setcheck=False 	 	# Sometimes setting the temp goes wrong and the first two digits are left out thats why we here check if the actual setpoint is the same as the desired setpoint, or sometimes the whole communication fails with rs232 port 
		i=0
		while setcheck==False:
			i=i+1
			self._set_temperature(temp)
			time.sleep(1)
			try:				 	 	 	 	 	# In case reading data leads to error, disconnect and reconnect (sometimes happens with Julabo)
				settemp = self._readtemp_set()
				setcheck = (settemp==temp or settemp == 0 )	# If settemp is '0', it is unimplemented for whatever reason and we continue without checking.
				if not setcheck: 	 	 	 	 	# If temperature was not set correctly, throw an error and handle together with 'real' errors
					raise serial.SerialException("the wrong temperature was set")
			except Exception as e:
				ex = str(e)
			
			if not setcheck:
				if i > 3:
					warnings.warn("Datatransfer failed %i times in a row, check connection. (I will not throw a real error, because sometimes feedback of machine doesn't work.)" % (i,) )
					break
				print("Something went wrong in datatransfer: %s.\nTrying again." % (ex, ))
				self.closecom() # close com and open again to try and restore data connection
				time.sleep(2)
				self.opencom()
							
		#self.closecom()
		print("Temperature set to %.2f deg C." % (temp,) )
	
class haake(Temperature_controller):
	'''
	DO NOT USE DIRECTLY, USE FOR INSTANCE 'haakeF6' OR 'haakePhoenix'!
	This is the class from which all Haake watherbaths can inherit - since the functions are the same anyway.
	If you change/add a function here, it changes for all Haake waterbaths.
	Cool innit?
	'''
	def __init__(self,comport):
		super().__init__(comport)
	
	def _readtemp_internal(self):
		'''
		Reads out internal temperature.
		'''
		readtemp_I_command = "F1\r"
		message = self._in_command(readtemp_I_command)
		return self._haake_temp_parser(message) # Which is temperature parsed from output
		
	def _readtemp_external(self):
		'''
		Reads out external temperature. Usefull if we add sensor to setup (which we won't do, but you know...).
		'''
		readtemp_E_command = "F2\r"
		message = self._in_command(readtemp_E_command)
		return self._haake_temp_parser(message) # Which is temperature parsed from output
	
	def _readtemp_set(self):
		'''
		Reads out set temperature.
		'''
		readtemp_S_command = "R SW\r"
		message = self._in_command(readtemp_S_command)
		return self._haake_temp_parser(message) # Which is temperature parsed from output
	
	def _set_temperature(self,temperature):
		'''
		Changes set temperature of waterbath. DO NOT USE DIRECTLY, USE haakeF6.changet() INSTEAD!
		'''
		settemp_command = "S  %i\r" % (round(float(temperature) * 100),)
		self._out_command( settemp_command )
		
		def _haake_temp_parser(self,message):
			'''
			Parses what the Haake returns into a readable temperature.
			The Haake returns something like 'SW+03100' which equals 31 degree C.
			'''
			try:
				return float(message[3:8])
			except ValueError:
				# Sorta quick hack: Sometimes, return format is different (for reasons I did not look into), so try other extraction type
				return float(message[5:10])
		
	def read_RTA_internal(self):
		'''
		Reads the internal temperature correction factor c.
		'''
		readRTA_I_command = "R CI\r"
		message = self._in_command( readRTA_I_command )
		c = float(message[2:9].decode())
		time.sleep(1)
		self._flush()
		return c,message
	
	def set_RTA_internal(self,setc):
		'''
		WARNING. THIS CHANGES THE CORRECTION FACTOR 'C', LEADING TO A DIFFERENT INTERNAL TEMPERATURE.
		NEVER CHANGE THIS IF YOU DO NOT NOW WHAT YOU ARE DOING!
		In case you screw up, +1.00 seems to be a sort of okay value.
 		'''
		setRTA_I_command = "W CI %.2f\r" % (setc,)
		self._out_command( setRTA_I_command )
		 
	def start_pump(self):
		startpump_command = "GO\r"
		self._out_command( startpump_command )
		
	def stop_pump(self):
		stoppump_command = "ST\r"
		self._out_command( stoppump_command )
	
	def alarm(self):
		alarm_command = "AL\r"
		self._out_command( alarm_command )
		
	def alarm_stop(self):
		alarm_stop_command = "ER\r"
		self._out_command( alarm_stop_command )
	
class haakeF6(haake):
	'''
	Class for controlling HaakeF6 waterbath.
	Inherits from haake superclass. Look there for the functions you might need.
	'''
	
	def __init__(self,comport):
		super().__init__(comport)
		self.com = self._initialize_connection (baudrate=4800,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=5,xonxoff=False,rtscts=False,write_timeout=5,dsrdtr=False,inter_byte_timeout=None)
		self.opencom()
		
		
class haakePhoenix(haake):
	'''
	Class for controlling Haake Phoenix C25P waterbath.
	Changing the temperature correction factor is not functional for unknown reasons, the rest is.
	Note that temperature given by the bath is of by about +0.8 degree C. (we cant correct internally due to weird non-functional RTA).
	Always start by starting the pump using haakePhoenix.start_pump(), as it does not start automatically.
	'''
	def __init__(self,comport):
		super().__init__(comport)
		self.com = self._initialize_connection(baudrate=9600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=5,xonxoff=False,rtscts=False,write_timeout=5,dsrdtr=False,inter_byte_timeout=None)
		self.opencom()

	
class julabo(Temperature_controller):
	'''
	Class for controlling Julabo F25 waterbath.
	(If we ever get another Julabo waterbath, we can convert this to a superclass like 'haake')
	'''
	
	def __init__(self,comport):
		super().__init__(comport)
		self.com = self._initialize_connection(4800,bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,timeout=5, xonxoff=False,rtscts=False,write_timeout=5,inter_byte_timeout=None)
		self.opencom()
		
	def _set_temperature(self,temperature):
		'''
		Changes set temperature of waterbath to 'temperature'. DO NOT USE DIRECTLY, USE changet() INSTEAD!
		'''
		settemp_command = "out_sp_00 %06.2f\r" % (float(temperature),)
		self._out_command( settemp_command )
			
	def status(self):
		'''
		Reads any messages or error codes from the machine.
		'''
		readtemp_I_command = "in_pv_00\r"
		message = self._in_command( readtemp_I_command )
		print(message)
	
	def _readtemp_set(self):
		'''
		Reads out set temperature.
		'''
		readtemp_S_command = "in_sp_00\r"
		message = self._in_command( readtemp_S_command )
		message_cleaned = str(message[0:-2])
		message_cleaned2 = message_cleaned.replace("\\xb","")
		message_cleaned3 = message_cleaned2[2:7]
		settemp = float(message_cleaned3)
		return settemp
	
	def _readtemp_internal(self):
		'''
		Reads out internal temperature.
		'''
		readtemp_I_command = "in_pv_00\r"
		message = self._in_command( readtemp_I_command )
		message_cleaned = str(message[0:-2])
		message_cleaned2 = message_cleaned.replace("\\xb","")
		message_cleaned3 = message_cleaned2[2:7]
		temp = float(message_cleaned3)
		return temp

	def start_pump(self):
		'''
		Starts the pump and heating/cooling elements of this waterbath.
		'''
		start_P_command = "out_mode_05 1\r"
		self._out_command( start_P_command )
		
	def stop_pump(self):
		'''
		Stops the pump and heating/cooling elements of this waterbath.
		'''
		stop_P_command = "out_mode_05 0\r"
		self._out_command( stop_P_command )
		
	def wiggle(self,temp,time=120):
		'''
		This is a TEMPORARY hack, to make sure Julabo stays connected to slow confocal.
		Works by changing T every 'time' seconds and almost immediatly changing it back.
		Just use "ctrl + c" to stop this, it runs ad infinitem.
		'''
		while True:
			self.changet(temp+0.01)
			time.sleep(2)
			self.changet(temp)
			for i in time:
				time.sleep(1)
		
class electric(Temperature_controller):
	'''
	Class for controlling the electric peltier-element-based heater.
	Note that we can control the temperature of the three components seperatly by
	calling electric.set_temperature_controller(temp,[2,3]). The self.changet and ramp function assume we want to ramp
	all three components at the same speed at the same temperature.
	WARNING: There is no feedback system in place yet to test whether data transfer is
	succesfull in the electric control unit. Thread carfully.
	'''
	def __init__(self,comport):
		super().__init__(comport)
		print('WARNING, the temperature will be set to 22.22 deg C to make sure the comport is configured correctly.')
		self.com = self._initialize_connection(9600,bytesize=serial.SEVENBITS,parity=serial.PARITY_EVEN,stopbits=serial.STOPBITS_TWO,timeout=5,xonxoff=False,rtscts=False,write_timeout=5,inter_byte_timeout=None)
		self.opencom()
		self.changet_all(22.22)
		
	def _datagenelec(self, temp, controller): #
		'''
		Generates data for command to electric control unit.
		enter temp as float (##.## - 2 decimals) and controllor as integer - 1,2 or 3.
		'''
		stx=b'\x02'
		etx=b'\x03'
		subadress=b'00'
		SID=b'0'

		controllerbit=('0'+str(controller)).encode('UTF-8')	# either 01,02,03
		command=b'0102C4000000000100000'					# for changing the set point of the first bank, which is what you want
		temp=int(round(temp*100)) 				 	#rounding 
		hexnmb=hex(temp)[2:].upper().encode('UTF-8')
		data=stx+controllerbit+subadress+SID+command+hexnmb+etx
		databcc = data + self._bcccalc(data)
		return databcc
		
	def _bcccalc(self,data):
		bcc=ord(chr(data[1]))
		for i in range(2,len(data)):
			bcc=bcc ^ ord(chr(data[i]))  
		return chr(bcc).encode('UTF-8')
		
	def _readtemp_set(self):
		'''
		Reads out set temperature.
		UNIMPLEMENTED FOR THE ELECTRIC CONTROLLER! RETURNS '0' TO PREVENT ERRORS
		'''
		return 0
		
	def set_temperature_controller(self,temperature,controller,verbose=True):
		'''
		Sets temperature for specified controllers
		'''
		if type(controller)==type(1):
			controller = [controller]
		for i in controller:
			settemp_command = self._datagenelec(temperature,i)
			self._out_command( settemp_command )
		if verbose:
			print("Temperature of controller(s) %s set to %.2f deg C." % (str(controller).strip('[]'),temperature) )
		
	def _set_temperature(self,temperature):
		'''
		Do not use direcly, use electric.changet(temp) instead.
		Sets temperature for *all* controllers. If you want to set individual ones, use electric.set_temperature_controller(temp,controllers).
		'''
		self.set_temperature_controller(temperature,[1,2,3],False)
		
class thermo(Temperature_controller):
	'''
	UNDER CONSTRUCTION.
	NOT READY FOR USE.
	ALSO, I DON'T KNOW WHICH WATERBATH THIS IS SUPPOSED TO BE, SO...
	'''
	
	def __init__(self,comport):
		super().__init__(comport)
		self.com = self._initialize_connection(9600,bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
		self.opencom()
		
	def _readtemp_set(self):
		self.com.write("RS\r".encode()) 
		time.sleep(1)
		readlength=self.com.inWaiting()
		#print(readlength)
		message=self.com.read(readlength)
		#print(message)
		settemp=float(message[3:8])
		return settemp
		