import serial
import serial.tools.list_ports # why these have to be seperate? Nobody knowsss. Also, this is only nessecary on Windows? Really weird stuff.
import time
import warnings
import math
import sys
import datetime
'''
@author: Piet Swinkels
Based on simonexp.py, written by Simon Stuij. I just put everything from simonexp.py in classes so that we can control two systems simultaniously. I also added support for haakeF6 and haakePhoenix, and made everything a bit more uniform.

IF YOU DON'T KNOW ANYTHING ABOUT PROGRAMING/THIS IS YOUR FIRST TIME HERE, READ HERE:
	1 Don't panic
	2 First run this script (there is a play button somehwere to do that)
	3 start by finding the USB port the heating unit is plugged in, type "find_available_comports(True)" in the screen to the right and press enter. read the help.
	4 Now, which waterbath are you using? Probably the Julabo one, I will continue as if you chose that.
	5 type "ju = julabo('the name you found in step 3')"
	6 You should be ready to do stuff now! Possible commands are:
		- 'ju.start_pump()' to start the waterbath
		- 'ju.changet(30)' to set the temperature to 30
		- 'ju.ramp_smooth(20,30,1000)' to change the temperature from 20 to 30 over the course of 1000 seconds.
	7 For help/more commands, ask Piet, or try reading the scripts. text between '' is mostly helpfull comments to look at.
		
This scripts requires the 'PySerial' module. The script should be able to work with  any version of this module (including very old ones that still work on Windows XP machines).

All these classes are used in a very similar way. First, we assign the class of the 
machine we want to use to a variable with the correct comport (see devices and printers), so for instance 'ju = julabo('com4')'. 
We can then trun on the pump by running self.start_pump(), set the temperature using self.changet(temp), and ramp the temperature using self.ramp(Tinit,Tend,dT,totaltime). All classes work exactly the same, although not all functionality is implemented in all classes.

Guide for adding new machines:
	* Every class should *at least* contain a function:
			- _readtemp_set (okay, not really, but is really inconvenient not to have this (looking at you electrical heating system)
			- _set_temperature
			These functions should contain a call to _in_command and _out command respectively, with the command found in the manual of the machine in question.
	* Let the class inherit from the superclass Temperature_controller, or, if we allready have a controller from the brand, the brand Superclass (i.e. 'haake').
	* Stuff should now work automatically

To be fixed/implemented:
	* At PC of fast&slow confocal, Julabo has the tendency to lose connection with PC if we don't invoke it often enough. This leads to a restart to restore connection. This is probably due to the windows XP they are running, not this script.

TODO:
	* Introduce some variable that stores the temperature at different moments in time?
		--> Use 'real' temperature vs. just storing temperature if we set it to something different.
	*Introduce a function that finds the possible ports (so you dont have to look for them somewhere.)
'''

# This checks if you are using a Windows XP machine, and if so, gives a small lecture about the dangers of Windows XP and serialports.
if 'win' in sys.platform:
	try:
		wv = sys.getwindowsversion()
		if wv.major <= 5: # If using windows 5 (WINDOWS XP) or below, give a warning
			print("*****I DETECT WINDOWS XP*****")
			time.sleep(1)
			warnings.warn("The serial ports have the tendency to loose connection when connected for extended periods of time without commands comming in on this version of Windows. Therefore, I advise using the 'wiggle' function as an alternative to 'changet'. This wiggles the temperature by 0.01 degrees every 2 minutes. This way, connection will not be lost and you will be safe!")
			time.sleep(1)
			print("*****END OF SAFETY MESSAGE*****")
	except:
		pass

def find_available_comports(helpme=False):
	'''
	This function just lists all COMports that are available.
	
	'''
	print("Available ports:")
	for i in serial.tools.list_ports.comports():
		print(i)
	if helpme:
		print("*******************HELP**********************")
		print("The PC has multiple ports to communicate with outside devices, such as USB ports, but also bluetooth. We must tell Python on which port is our machine. Because the temp-controllers use a 'serial RS232' port, and this computer only has usb-ports, we use a converter. Each PC has a different brand converter, so thats why I cant just select one automatically. The list just printed will contain a comport name (i.e., 'COM4', or 'tty0') and a description. The description tells you what is attached to the PC. In this case we are looking for somethin along the lines of 'USB-to-Serial Conversion' or whatever. Remember the corresponding COMport name, and input that into the regular script. And that's it. Easypeasy." )
		

class Temperature_controller():
	'''
	This is the superclass (metaclass). It cannot be used directly, but all temperature controllers inherit from it. 
	So, basically, if you change something here, it will change something in all classes. Usefull for things that all classes do, so for instance the ramping function.
	This Class has great power, use with great responsibility.
	'''
	def __init__(self,comport):
		self.comport = comport
	
	def __repr__(self):
		message = " <%s object controlling comport %s>" % (str(self.__class__),self.comport)
		return message 
	
	def __str__(self):
		'''
		This is returned if you do print(Temperature_controller)
		'''
		message = "Connection to Temperature_controller at comport:\t%s\nInternal temperature is currently:\t%.2f\nSet temperature is currently:\t%.2f\n" % (self.comport,self._readtemp_internal(),self._readtemp_set())
		return message
	
	def _initialize_connection (self,baudrate,bytesize,parity,stopbits,timeout=None,xonxoff=False,rtscts=False,write_timeout=None,dsrdtr=False,inter_byte_timeout=None):
		'''
		Does what you think it does. It makes a connection to the waterbathe with given parameters.
		'''
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
		
	def _out_command(self,command,flush=True):
		'''
		Setting values of parameters. Does not return anything. Fot instance, can set the temperature.
		Has error catching mechanism --> sometimes "SerialException: WriteFile failed (PermissionError(13, 'The device does not recognize the command.', None, 22))" is thrown after long stretch of inactivity. Manually, you can solve this by just restarting 'ju = julabo('com4')' etc.. This is an attempt to do this automatically, so a ramp or something will not be disturbed.
		'''
		try:
			self.com.write( command.encode() )
		except serial.SerialException:
			print('I detected that the connection to the device has been interupted. I will try to reset the connection. This may fail!')
			print(">>> REINITIALISING CONNECTION <<<")
			self.__init__(self.comport)
			self.com.write( command.encode() )
			print(">>>REINITIALISATION SUCCESFULL<<<")
		if flush:
			self._flush() # To remove command from buffer
		
	def _in_command(self,command):
		'''
		Asking for parameters or temperatures to be returned by waterbath. Returns raw message.
		'''
		self._out_command(command,False) # use _out_command to send message
		time.sleep(0.1)
		readlength=self.com.inWaiting()
		message = self.com.read(readlength)
		self._flush() # to remove command(and answer) from buffer
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
		
	def ramp(self,Tinit,Tend,dT,totaltime,ask=True,verbose=False):
		'''
		Makes a block temperature ramp with device for controlling temperature.

		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Temperature step of ramp in deg C.
			* totaltime : Total time of measurement in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		
		t00 = time.clock() 	 	 	 	 	 	 	 	 	# Initialize internal clock (in seconds)
		steps = abs(round((Tend-Tinit)/dT))	 	 		 	# Number of steps
		if Tinit > Tend: # Ramp down
			Trange = [round(Tinit - i*dT,2) for i in range(0,steps+1)] # Temperatures we will visit
		elif Tinit < Tend: # Ramp up
			Trange = [round(Tinit + i*dT,2) for i in range(0,steps+1)] # Temperatures we will visit
		else:
			raise ValueError('Detected problem with either Tinit or Tend value, they are probably equal.')
		
		print('Temperature range is given by:\n'+str(Trange))
		
		waittime = totaltime / len(Trange) 						# Waiting time between steps in sec
		fwaittime = str(datetime.timedelta(seconds=waittime))	# Formatted time for display
		ftotaltime = str(datetime.timedelta(seconds=totaltime))	# Idem dito
		
		print('The waiting time between each step is %s.' % (fwaittime,))
		if waittime <= 10:
			warnings.warn("The waiting step between 2 temperatures is probably to small for the waterbath to keep up. I suggest you try using a longer time.",)
		print('The total time of this ramp is %s.' % (ftotaltime,))
		
		if ask:
			test = input("Press enter to start ramp, press q to abort.")
			if 'q' in test:
				raise ValueError("Aborted measurement before start.")
			else:
				pass
			
		t0=time.clock()
		ft0 = str(datetime.timedelta(seconds=t0))
		
		if verbose:
			print('Starting at internal clock time: %s.' % (ft0,))
		
		print('Starting ramp at:', datetime.datetime.now())
		
		for T in Trange:
			tnew = time.clock()
			tbeforechange = time.clock()
			if verbose:
				ftnew = str(datetime.timedelta(seconds=round(time.clock())))
				print('Internal time - %s\t-\t Changing temperature to %.2f deg C...' % (ftnew,T))
				
			print(datetime.datetime.now().time(), "- Changing temperature to %.2f deg C..." % (T,))
			pasttime = int(round(tnew-t0))
			fpasttime = str(datetime.timedelta(seconds=pasttime))
			ftnew = str(datetime.timedelta(seconds=round(time.clock())))
			
			if verbose:
				fpasttime = str(datetime.timedelta(seconds=pasttime))
				ftnew = str(datetime.timedelta(seconds=round(time.clock())))
				print('Time past since last temperature change: %s.' % (fpasttime,))
				print('Internal time at changing Temperature - %s' % (ftnew,))
				#print('difference in time before last change not rounded '+str(tnew-t0))
			
			
			self.changet(T)
			tafterchange = time.clock()
			
			tcorrection = tafterchange-tbeforechange
			
			if verbose:
				print('time it took to change Temperature '+str(round(tcorrection)))
				print('time it took to change Temperature not rounded '+str(tcorrection))
			
			# This weird thing makes it possible to interrupt sleeping
			slptime = math.floor(waittime-tcorrection)
			for i in range(slptime):
				time.sleep(1)
			time.sleep(waittime-tcorrection-slptime)
			
		ffinaltime = str(datetime.timedelta(seconds=round(time.clock()-t00)))
		print('Ramp completed.\nTotal time of the ramp: %s.' % (ffinaltime,) )


	def ramp_steptime(self,Tinit,Tend,dT,steptime,ask=True,verbose=False):
		'''
		Equivalent to ramp(), but uses steptime instead of totaltime	
		Makes a block temperature ramp with device for controlling temperature.

		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* dT        : Tempearture step of ramp in deg C.
			* steptime  : Total time of a step in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		steps = abs(round((Tend-Tinit)/dT))	 	 		 	 	 	# Number of steps
		Trange = [round(Tinit + i*dT,2) for i in range(0,steps+1)] # Temperatures we will visit
		totaltime = len(Trange) * steptime
		self.ramp(Tinit,Tend,dT,totaltime,ask,verbose)
	
	def ramp_smooth(self,Tinit,Tend,totaltime,ask=True,verbose=False):
		'''
		Equivalent to ramp(), but with dT = 0.01 preset.
		Makes a continues temperature ramp (or as close to it as we can with our setup) with device for controlling temperature.

		IN:
			* Tinit     : Start temperature of ramp in deg C.
			* Tend      : Final temperature of ramp in deg C.
			* totaltime : Total time of the experiment in *seconds*.
			* ask       : Boolean, if True, will give all experimental info and wait for user conformation. If False, it will just start.
			* verbose   : Boolean, set to True to get all debug info.
		'''
		dT = 0.01
		self.ramp(Tinit,Tend,dT,totaltime,ask,verbose)
		
	def changet(self,temp):
		"""
		Changes temperature of temperature control unit to temp, and checks if it was succesfull.
		Number will be rounded to 2 decimals. Also print current time because that can be useful.
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
					warnings.warn("Datatransfer failed %i times in a row, try diconnecting and reconnecting the usb cable. I will not throw a real error, because sometimes feedback of machine doesn't work, while temperature is changed corretly." % (i,) )
					break
				print("Something went wrong in datatransfer: %s.\nTrying again." % (ex, ))
				self.closecom() # close com and open again to try and restore data connection
				time.sleep(2)
				self.opencom()
							
		#self.closecom()
		if i>1 and setcheck==True:
			print("Recovered from error(s) succesfully.")
		
		# Print confirmation of temperature setting, and current time because usefull.
		print(datetime.datetime.now().time(),"- Temperature set to %.2f deg C." % (temp,) )
	
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
		The Haake returns something like b'$\r\nSW+033.99$\r\n' which equals +33.99 degree C.
		'''
		#print(message) #For debug
		try:
			return float(message[2:9])
		except ValueError:
			# Sorta quick hack: Sometimes, return format is different (it adds leading '$\r\n' for reasons I did not look into), so try other extraction type
			try:
				return float(message[5:12])
			# If it still doesn't work, give detailed error response.
			except Exception as e:
				#print(e) #For debug
				raise ValueError("Parser could not read haake response: '%s'" % (str(message),))

	def read_RTA_internal(self):
		'''
		Reads the internal temperature correction factor c.
		'''
		readRTA_I_command = "R CI\r"
		message = self._in_command( readRTA_I_command )
		c = self._haake_temp_parser( message )
		time.sleep(1)
		self._flush()
		return c,message
	
	def set_RTA_internal(self,setc):
		'''
		WARNING. THIS CHANGES THE CORRECTION FACTOR 'C', LEADING TO A DIFFERENT INTERNAL TEMPERATURE.
		NEVER CHANGE THIS IF YOU DO NOT NOW WHAT YOU ARE DOING!
		In case you screw up, +0.50 seems to be a sort of okay value.
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
		self.com = self._initialize_connection (baudrate=4800,
										  bytesize=serial.EIGHTBITS,
										  parity=serial.PARITY_NONE,
										  stopbits=serial.STOPBITS_ONE,
										  timeout=5,
										  xonxoff=False,
										  rtscts=False,
										  write_timeout=5,
										  dsrdtr=False,
										  inter_byte_timeout=None)
		self.opencom()
		
		
class haakePhoenix(haake):
	'''
	Class for controlling Haake Phoenix C25P waterbath.
	Changing the temperature correction factor is not functional for unknown reasons, the rest works fine.
	Note that temperature given by the bath is of by about +0.8 degree C. (we cant correct internally due to weird non-functional RTA).
	Always start by starting the pump using haakePhoenix.start_pump(), as it does not start automatically.
	'''
	def __init__(self,comport):
		super().__init__(comport)
		self.com = self._initialize_connection(baudrate=9600,
										 bytesize=serial.EIGHTBITS,
										 parity=serial.PARITY_NONE,
										 stopbits=serial.STOPBITS_ONE,
										 timeout=5,
										 xonxoff=False,
										 rtscts=False,
										 write_timeout=5,
										 dsrdtr=False,
										 inter_byte_timeout=None)
		self.opencom()

	
class julabo(Temperature_controller):
	'''
	Class for controlling Julabo F25 waterbath.
	(If we ever get another Julabo waterbath, we can convert this to a superclass like 'haake')
	'''
	
	def __init__(self,comport):
		super().__init__(comport)
		self.com = self._initialize_connection(baudrate = 4800,
										 bytesize=serial.EIGHTBITS,
										 parity=serial.PARITY_NONE, 
										 stopbits=serial.STOPBITS_ONE,
										 timeout=5,
										 xonxoff=False,
										 rtscts=False,
										 write_timeout=5,
										 inter_byte_timeout=None)
		self.opencom()
		
	def _julabo_temp_parser(self,message):
		'''
		in:
			message - Raw output of the Julabo which contains temperature.
		out:
			Float representing the temperature in degree Celsius.
			
		The output of the Julabo looks something like this:
			b'\xb26.33\x8d\n'
		in which 26.33 is the temperature in Celsius.
		'''
		message_cleaned = str(message[0:-2])
		message_cleaned2 = message_cleaned.replace("\\xb","")
		message_cleaned3 = message_cleaned2[2:7]
		return float(message_cleaned3)
		
		
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
		settemp = self._julabo_temp_parser(message)
		return settemp
	
	def _readtemp_internal(self):
		'''
		Reads out internal temperature.
		'''
		readtemp_I_command = "in_pv_00\r"
		message = self._in_command( readtemp_I_command )
		temp = self._julabo_temp_parser(message)
		return temp
	
	def _readtemp_external(self):
		readtemp_E_command = "in_pv_02\r"
		message = self._in_command( readtemp_E_command )
		print('Julabo returns:',message) # For debug
		temp = self._julabo_temp_parser(message)
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
		self.com = self._initialize_connection(9600,
										 bytesize=serial.SEVENBITS,
										 parity=serial.PARITY_EVEN,
										 stopbits=serial.STOPBITS_TWO,
										 timeout=5,
										 xonxoff=False,
										 rtscts=False,
										 write_timeout=5,
										 inter_byte_timeout=None)
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
		