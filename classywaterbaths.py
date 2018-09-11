import serial
import time
import warnings

'''
@author: Piet Swinkels
Based on simonexp.py, written by Simon Stuij. I just put everything from simonexp.py in classes so that we can control 
two systems simultaniously. I also added support for haakeF6 and haakePhoenix, and made everything a bit more uniform.


All these classes are used in a very similar way. First, we assign the class of the 
machine we want to use to a variable with the corect comport (see devices and printers). 
We can then set the temperature using self.changet(temp), and ramp the temperature
using self.ramp(Tinit,Tend,dT,totaltime). Note that all machines/classes have their
own quirks, you should probably read the code before using it. Or at least ask someone about it. Please.

Guide for adding new machines:
	* Every class should *at least* contain a function:
			- _initialize_connection (called at __init__)
			- closecom
			- opencom
			- _flush
			- _readtemp_set
			- _set_temperature
			- changet (should refer to general _changet function)
			- ramp (refer to general _ramp function)		
		if not, we must hack our way around, but this should NOT be done lightly.

To be fixed/implemented:
	* At PC of slow confocal, Julabo has the tendency to lose connection with PC if we don't invoke it often enough. This leads to forced restart.
		--> Is this general for all waterbaths?
		--> Is this general for all PC's?
		--> Is it code or hardware related?
		
	* Introduce some variable that stores the temperature at different moments in time?
		--> Use 'real' temperature vs. just storing temperature if we set it to something different.
'''

class haakeF6:
	'''
	Class for controlling HaakeF6 waterbath.
	When finished, please call haakeF6.closecom() to prevent errors for the next user.
	'''
	def __init__(self,comport):
		self.comport = comport
		self.com = self._initialize_connection()
		
	def __str__(self):
		message = "Connection to Haake F6 at comport:\t%s\nInternal temperature is currently:\t%.2f\nSet temperature is currently:\t%.2f\n" % (self.comport,self._readtemp_internal(),self._readtemp_set())

		return message
	
	def __repr__(self):
		message = " <%s object controlling comport %s>" % (str(self.__class__),self.comport)
		return message
	
	def _initialize_connection(self):
		try: 
			return serial.Serial(self.comport,baudrate=4800,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=None,xonxoff=False,rtscts=False,write_timeout=None,dsrdtr=False,inter_byte_timeout=None)
		except serial.SerialException:
			raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc)')
	
	def closecom(self):
		if self.com.isOpen(): 
			self.com.close()
	
	def opencom(self):
		if not self.com.isOpen(): 
			self.com.open()  #open if comport is closed
		
	def _readtemp_internal(self):
		'''
		Reads out internal temperature.
		'''
		self.opencom()
		readtemp_I_command = "F1\r"
		self.com.write( readtemp_I_command.encode() )
		time.sleep(1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		temp = float(message[3:8])
		time.sleep(1)
		self._flush()
		self.closecom()
		return temp
		
	def _readtemp_external(self):
		'''
		Reads out external temperature. Usefull if we add sensor to setup.
		'''
		self.opencom()
		readtemp_E_command = "F2\r"
		self.com.write( readtemp_E_command.encode() )
		time.sleep(1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		temp = float(message[3:8])
		time.sleep(1)
		self._flush()
		self.closecom()
		return temp
	
	def _readtemp_set(self):
		'''
		Reads out set temperature.
		'''
		self.opencom()
		readtemp_S_command = "R SW\r"
		self.com.write( readtemp_S_command.encode() )
		time.sleep(1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		temp = float(message[4:9])
		time.sleep(1)
		self._flush()
		self.closecom()
		return temp
	
	def _set_temperature(self,temperature):
		'''
		Changes set temperature of waterbath. DO NOT USE DIRECTLY, USE haakeF6.changet() INSTEAD!
		'''
		self.opencom()
		settemp_command = "S  %i\r" % (round(float(temperature) * 100),)
		self.com.write( settemp_command.encode() )
		time.sleep(1)
		self._flush()
		self.closecom()
		
	def _flush(self):
		self.com.flushInput()
		self.com.flushOutput()
	
	def read_RTA_internal(self):
		'''
		Reads the internal temperature correction factor c.
		'''
		self.opencom()
		readRTA_I_command = "R CI\r"
		self.com.write( readRTA_I_command.encode() )
		time.sleep(1)
		readlength = self.com.inWaiting()
		message = self.com.read(readlength)
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
		self.opencom()
		setRTA_I_command = "W CI %.2f\r" % (setc,)
		self.com.write( setRTA_I_command.encode() )	
		self._flush() 
		self.closecom()
		 
	def start_pump(self):
		self.opencom()
		startpump_command = "GO\r"
		self.com.write( startpump_command.encode() )
		self._flush()
		self.closecom()
		
	def stop_pump(self):
		self.opencom()
		stoppump_command = "ST\r"
		self.com.write( stoppump_command.encode() )
		self._flush()
		self.closecom()
	
	def alarm(self):
		self.opencom()
		alarm_command = "AL\r"
		self.com.write( alarm_command.encode() )
		self._flush()
		self.closecom()
		
	def alarm_stop(self):
		self.opencom()
		alarm_stop_command = "ER\r"
		self.com.write( alarm_stop_command.encode() )
		self._flush()
		self.closecom()
		
	def changet(self,temp):
		"""
		Changes temperature of waterbath, and checks if it was succesfull.
		Number will be rounded to 2 decimals.
		"""
		_changet(temp,self)
		print("Temperature set to %.2f deg C." % (temp,) )
		
	def ramp(self,Tinit,Tend,dT,totaltime,ask=True,verbose=False):
		'''
		Makes a block tempramp with the Haake. 
		Uses _ramp() internally.
		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Tempearture step of ramp in deg C.
			* totaltime : Total time of measurement in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		_ramp(Tinit,Tend,dT,totaltime,ask,self,verbose)

class haakePhoenix:
	'''
	Class for controlling Haake Phoenix C25P waterbath.
	When finished, please call haakePhoenix.closecom() to prevent errors for the next user.
	Changing the temperature correction factor is not functional for unknown reasons, the rest is.
	Note that temperature given by the bath is of by about +0.8 degree C.
	Always start by strating the pump using haakePhoenix.start_pump(), as it does not start automatically.
	'''
	def __init__(self,comport):
		self.comport = comport
		self.com = self._initialize_connection()
		
	def __repr__(self):
		message = " <%s object controlling comport %s>"  % (str(self.__class__),self.comport)
		return message
	
	def __str__(self):
		message = "Connection to Haake Phoenix at comport:\t%s\nInternal temperature is currently:\t%.2f\nSet temperature is currently:\t%.2f\n" % (self.comport,self._readtemp_internal(),self._readtemp_set())
		return message
	
	def _initialize_connection(self):
		try: 
			return serial.Serial(self.comport,baudrate=9600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=None,xonxoff=False,rtscts=False,write_timeout=None,dsrdtr=False,inter_byte_timeout=None)
		except serial.SerialException:
			raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc)')
	
		
	def closecom(self):
		if (self.com.isOpen() == True): 
			self.com.close()
	
	def opencom(self):
		if (self.com.isOpen() == False): 
			self.com.open()  #open if comport is closed
		
	def _readtemp_internal(self):
		'''
		Reads out internal temperature.
		'''
		self.opencom()
		readtemp_I_command = "F1\r"
		self.com.write( readtemp_I_command.encode() )
		time.sleep(1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		temp = float(message[3:8])
		self._flush()
		self.closecom()
		return temp
		
	def _readtemp_external(self):
		'''
		Reads out external temperature. Usefull if we add sensor to setup.
		'''
		self.opencom()
		readtemp_E_command = "F2\r"
		self.com.write( readtemp_E_command.encode() )
		time.sleep(1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		temp = float(message[3:8])
		self._flush()
		self.closecom()
		return temp
	
	def _readtemp_set(self):
		'''
		Reads out set temperature.
		'''
		self.opencom()
		readtemp_S_command = "R SW\r"
		self.com.write( readtemp_S_command.encode() )
		time.sleep(1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		temp = float(message[4:9])
		self._flush()
		self.closecom()
		return temp
	
	def _set_temperature(self,temperature):
		'''
		Changes set temperature of waterbath. DO NOT USE DIRECTLY, USE changet() INSTEAD!
		'''
		self.opencom()
		settemp_command = "S  %i\r" % (round(float(temperature) * 100),)
		self.com.write( settemp_command.encode() )
		self._flush()
		self.closecom()
		
	def _flush(self):
		self.com.flushInput()
		self.com.flushOutput()
	
	def read_RTA_internal(self):
		'''
		Reads the internal temperature correction factor c.
		'''
		self.opencom()
		readRTA_I_command = "R CI\r"
		self.com.write( readRTA_I_command.encode() )
		time.sleep(1)
		readlength = self.com.inWaiting()
		message = self.com.read(readlength)
		c = float(message[2:9].decode())
		self._flush()
		self.closecom()
		return c
	
	def set_RTA_internal(self,setc):
		'''
		THIS FUNCTION DOES NOT WORK FOR SOME REASON!
		WARNING. THIS CHANGES THE CORRECTION FACTOR 'C', LEADING TO A DIFFERENT INTERNAL TEMPERATURE.
		NEVER CHANGE THIS IF YOU DO NOT NOW WHAT YOU ARE DOING!
		In case you screw up, +0.70 seems to be a sort of okay value.
 		'''
		self.opencom()
		setRTA_I_command = "W CI %.2f\r" % (setc,)
		self.com.write( setRTA_I_command.encode() )	
		self._flush() 
		self.closecom()
		 
	def start_pump(self):
		self.opencom()
		startpump_command = "GO\r"
		self.com.write( startpump_command.encode() )
		self._flush()
		self.closecom()
		
	def stop_pump(self):
		self.opencom()
		stoppump_command = "ST\r"
		self.com.write( stoppump_command.encode() )
		self._flush()
		self.closecom()
	
	def alarm(self):
		self.opencom()
		alarm_command = "AL\r"
		self.com.write( alarm_command.encode() )
		self._flush()
		self.closecom()
		
	def alarm_stop(self):
		self.opencom()
		alarm_stop_command = "ER\r"
		self.com.write( alarm_stop_command.encode() )
		self._flush()
		self.closecom()
		
	def changet(self,temp):
		_changet(temp,self)

	def ramp(self,Tinit,Tend,dT,totaltime,ask=True,verbose=False):
		'''
		Makes a block tempramp with the Haake. 
		Uses _ramp() internally.
		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Tempearture step of ramp in deg C.
			* totaltime : Total time of measurement in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		_ramp(Tinit,Tend,dT,totaltime,ask,self,verbose)
	
	def loop(self,loopnmb,Thigh,Tlow,Thigh_time,Tlow_time):
		for i in range(loopnmb):
			self.changet(Thigh)
			time.sleep(Thigh_time)
			self.changet(Tlow)
			time.sleep(Tlow_time)
		
class julabo:
	'''
	Class for controlling Julabo F25 waterbath.
	'''
	
	def __init__(self,comport):
		self.comport = comport
		self.com = self._initialize_connection()
	
	def __repr__(self):
		message = " <%s object controlling comport %s>"  % (str(self.__class__),self.comport)
		return message
	
	def __str__(self):
		message = "Connection to Julabo at comport:\t%s\nInternal temperature is currently:\t%.2f degC\nSet temperature is currently:\t\t%.2f degC" % (self.comport,self._readtemp_internal(),self._readtemp_set())
		return message
	
	def _initialize_connection(self):
		try:
			return serial.Serial(self.comport,4800,bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,timeout=1, xonxoff=0,rtscts=0)
		except serial.SerialException:
			raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc).')
	
	def _set_temperature(self,temperature):
		'''
		Changes set temperature of waterbath to 'temperature'. DO NOT USE DIRECTLY, USE changet() INSTEAD!
		'''
		self.opencom()
		settemp_command = "out_sp_00 %06.2f\r" % (float(temperature),)
		self.com.write( settemp_command.encode() )
		self._flush()
		self.closecom()
	
	def closecom(self):
		if (self.com.isOpen() == True): 
			self.com.close()
	
	def opencom(self):
		if (self.com.isOpen() == False): 
			self.com.open()  #open if comport is closed
			
	def status(self):
		'''
		Reads any messages or error codes from the machine.
		'''
		self.opencom()
		readtemp_I_command = "in_pv_00\r"
		self.com.write( readtemp_I_command.encode() )
		time.sleep(1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		self._flush()
		self.closecom()
		print(message)
	
	def _readtemp_set(self):
		'''
		Reads out set temperature
		'''
		self.opencom()
		self.com.write("in_sp_00\r".encode())
		time.sleep(1)
		readlength=self.com.inWaiting()
		message=self.com.read(readlength)
		#print(message)         # usefull in debug
		message_cleaned=str(message[0:-2])
		message_cleaned2=message_cleaned.replace("\\xb","")
		message_cleaned3=message_cleaned2[2:7]
		settemp=float(message_cleaned3)
		self._flush()
		self.closecom()
		return float(settemp)
	
	def _readtemp_internal(self):
		'''
		Reads out internal temperature.
		NOT TESTED, TRY FIRST.
		'''
		self.opencom()
		readtemp_I_command = "in_pv_00\r"
		self.com.write( readtemp_I_command.encode() )
		time.sleep(1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		message_cleaned = str(message[0:-2])
		message_cleaned2 = message_cleaned.replace("\\xb","")
		message_cleaned3 = message_cleaned2[2:7]
		temp = float(message_cleaned3)
		self._flush()
		self.closecom()
		return temp

	def _flush(self):
		self.com.flushInput()
		self.com.flushOutput() 
	
	def start(self):
		'''
		For convenience. In the formalism of this script, you should use start_pump().
		'''
		self.com.open() 
		self.com.write("out_mode_05 1\r".encode())
		self._flush()
		self.com.close()
	
	def stop_pump(self):
		self.com.open() 
		self.com.write("out_mode_05 0\r".encode())
		self._flush()
		self.com.close()
		
	def changet(self,temp):
		"""
		Changes temperature to 'temp'. 'temp' should be of form ##.## .
		Uses _changet() internally.
		"""
		_changet(temp,self)
		
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
		
	def ramp(self,Tinit,Tend,dT,totaltime,ask=True,verbose=False):		
		'''
		Makes a block tempramp with the Julabo. 
		Uses _ramp() internally.
		IN:
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Tempearture step of ramp in deg C.
			* totaltime : Total time of measurement in *seconds*.
			* Tinit     : Start temperature of ramp in deg C.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		_ramp(Tinit,Tend,dT,totaltime,ask,self,verbose)
		
class electric:
	'''
	Class for controlling the electric, peltier element based, heater.
	Note that we can control the temperature of the three components seperatly by
	calling self.changet(temp,[1 or 2 or 3]). The self.ramp function assumes ramping
	all three components at the same speed at the same temperature.
	WARNING: There is no feedback system in place to test whether data transfer is
	succesfull in the electric control unit. Thread carfully.
	'''
	def __init__(self,comport):
		self.comport = comport
		print('WARNING, the temperature will be set to 22.22 deg C to make sure the comport is configured correctly.')
		self.com = self._initialize_connection()
		self.changet_all(22.22)
	
	def __repr__(self):
		message = " <%s object controlling comport %s>"  %  (str(self.__class__),self.comport)
		return message
	
	def _initialize_connection(self):
		try:
			return serial.Serial(self.comport, 9600, bytesize=7, parity=serial.PARITY_EVEN, stopbits=2, xonxoff=0, rtscts=0, timeout=1)
		except serial.SerialException:
			raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc).')
	
	def _flush(self):
		self.com.flushInput()
		self.com.flushOutput()
	
	def closecom(self):
		if (self.com.isOpen() == True): 
			self.com.close()
	
	def opencom(self):
		if (self.com.isOpen() == False): 
			self.com.open()  #open if comport is closed
	
	def _datagenelec(self, temp, controller): #
		'''
		enter temp as float (##.## - 2 decimals) and controllor as integer - 1,2 or 3.
		'''
		stx=b'\x02'
		etx=b'\x03'
		subadress=b'00'
		SID=b'0'

		controllerbit=('0'+str(controller)).encode('UTF-8')	#either 01,02,03
		command=b'0102C4000000000100000'			#for changing the set point of the first bank, which is what you want
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
	
	def changet(self, temp, controller=[1,2,3],verbose=True):
		'''
		Changes temperature of one of the components of the electric heater.
		WARNING: There is no feedback system in place to test whether data transfer is
		succesfull. Thread carfully.
		Enter temp as float (##.## - 2 decimals) and controllor as integer or list - 1,2 or 3/ [1,2,3]/ etc..
		'''
		if type(controller)==type(1):
			controller = [controller]
		
		for i in controller:
			data=self._datagenelec(temp,i)
			self.com.close()
			self.com.open()
			self.com.write(data)
		if verbose:
			print("Temperature of controller(s) %s set to %.2f deg C." % (str(controller).strip('[]'),temp) )
		
	def changet_all(self,temp):
		'''
		Changes temperature of all the components of the electric heater.
		Enter temperature as float (##.## - 2 decimals).
		'''
		self.changet(temp, [1,2,3], False)
		print("Temperature of all controllers set to %.2f deg C." % (temp,) )
		
	def ramp(self,Tinit,Tend,dT,totaltime,ask=True,verbose=False):
		'''
		Makes a block tempramp with the electronically controlled temperature unit. 
		There is no feedback control for this unit, so you should check if stuff really works!
		Ramp only works if we use all controllers. Otherwise, rewrite stuff or do manually.
		Uses _ramp() internally.
		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Tempearture step of ramp in deg C.
			* totaltime : Total time of measurement in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		_ramp(Tinit,Tend,dT,totaltime,ask,self,verbose)
		
	
class thermo:
	'''
	UNDER CONSTRUCTION.
	NOT READY FOR USE
	'''
	
	def __init__(self,comport):
		self.comport = comport
		self.com = self._initialize_connection()
		
	def __repr__(self):
		message = " <%s object controlling comport %s>"  %  (str(self.__class__),self.comport)
		return message
	
	def _initialize_connection(self):
		try:
			return serial.Serial(self.comport,9600,bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
		except serial.SerialException:
			raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc).')

	def _readtemp_set(self):
		self.com.write("RS\r".encode()) 
		time.sleep(1)
		readlength=self.com.inWaiting()
		#print(readlength)
		message=self.com.read(readlength)
		#print(message)
		settemp=float(message[3:8])
		return settemp
	
	def _flush(self):
		self.com.flushInput()
		self.com.flushOutput()
	
	def changet(self,temp):
		"""
		temp should be of form ##.##
		"""
		_changet(temp,self)
		
	def ramp(self,Tinit,Tend,dT,totaltime,ask=True,verbose=False):
		'''
		Makes a block tempramp with the Thermo. 
		Uses _ramp() internally.
		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Tempearture step of ramp in deg C.
			* totaltime : Total time of measurement in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		_ramp(Tinit,Tend,dT,totaltime,ask,self,verbose)


# The following are general functions used by all classses. Changing the behaviour of this will change behaviour of all classes! 
def _ramp(Tinit,Tend,dT,totaltime,ask,self,verbose=False):
	'''
	Makes a block temperature ramp with device for controlling temperature.
	Used internally by all device classes.
	NEVER use directly!
	IN:
		* Tinit     : Start temperature of ramp in deg C.
		* Tend      : Final temperature of ramp in deg C.
		* dT        : Tempearture step of ramp in deg C.
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
		time.sleep(waittime-tcorrection)
	print('Total time of the measurement: %.2f minutes / %.2f hours.' % ((time.clock()-t00) / 60 , (time.clock()-t00) /60/60) )

        
def _ramp_steptime(Tinit,Tend,dT,steptime,ask,self,verbose=False):
	'''
	Equivalent to _ramp(), but uses steptime instead of totaltime	
	Makes a block temperature ramp with device for controlling temperature.
	Used internally by all device classes.
	NEVER use directly!
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
	_ramp(Tinit,Tend,dT,totaltime,ask,self,verbose)

def _ramp_smooth(Tinit,Tend,totaltime,ask,self,verbose):
	'''
	Equivalent to _ramp(), but with dT = 0.01 preset.
	Makes a continues temperature ramp (as much as we can with our setup) with device for controlling temperature.
	Used internally by all device classes.
	NEVER invoke directly!
	IN:
		* Tinit     : Start temperature of ramp in deg C.
		* Tend      : Final temperature of ramp in deg C.
		* totaltime : Total time of the experiment in *seconds*.
		* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
		* self      : The object used to control temperature device.
		* verbose   : Boolean, set to True to get all debug info.
	'''
	dT = 0.01
	_ramp(Tinit,Tend,dT,totaltime,ask,self,verbose)
	
def _changet(temp,self):
	"""
	Changes temperature of temperature control unit 'self' to temp, and checks if it was succesfull.
	Number will be rounded to 2 decimals.
	*NEVER* invoke this function directly!
	"""
	temp = round(temp,2) 	# In case somebody still puts in ##.###, note that ##.# or ## is no problem
	
	self.opencom()
  
	setcheck=False 	 	# Sometimes setting the temp goes wrong and the first two digits are left out thats why we here check if the actual setpoint is the same as the desired setpoint
						# Or sometimes the whole communication fails with rs232 port 
	i=0
	while setcheck==False:
		i=i+1
		self._flush()       
		self._set_temperature(temp)
		time.sleep(1)
		try:				 	 	 	 	 	# In case reading data leads to error, disconnect and reconnect (sometimes happens with Julabo)
			settemp = self._readtemp_set()
			setcheck = (settemp==temp)			
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
						
	self.closecom()
	print("Temperature set to %.2f deg C." % (temp,) )