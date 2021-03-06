'''
@author: Piet Swinkels
Based on simonexp.py, written by Simon Stuij. I just put everything from simonexp.py in classes so that we can control two systems simultaniously. I also added support for haakeF6 and haakePhoenix, and made everything a bit more uniform.

IF YOU DON'T KNOW ANYTHING ABOUT PROGRAMING/THIS IS YOUR FIRST TIME HERE, READ HERE:
    1 Don't panic
    2 First run this script (there is a play button somehwere to do that)
    3 start by finding the USB port the heating unit is plugged in, type "find_available_comports(True)" in the screen to the right and press enter. read the help.
    4 Now, which waterbath are you using? Probably the Julabo one, I will continue as if you chose that.
    5 type "ju = julabo('[the name you found in step 3]')"
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
    * Let the class inherit from the metaclass Temperature_controller, or, if we allready have a controller from the brand, the brand metaclass (i.e. 'haake').
    * Stuff should now work automatically

Random Notes:
    * On Linux machines, plugged in devices are by default not accesible without sudo. Use this to make it accesible by default: https://stackoverflow.com/questions/27858041/oserror-errno-13-permission-denied-dev-ttyacm0-using-pyserial-from-pyth

To be fixed/implemented:
    * At PC of fast&slow confocal, Julabo has the tendency to lose connection with PC if we don't invoke it often enough. This leads to a restart to restore connection. This is probably due to the windows XP they are running, not this script.

TODO:
    * Introduce some variable that stores the temperature at different moments in time?
        --> Use 'real' temperature vs. just storing temperature if we set it to something different.
    * Debug new LAUDA Ecoline E200
'''

import serial
import serial.tools.list_ports
import time
import warnings
import math
import sys
import datetime
import logging

def find_available_comports(helpme=False):
    '''
    This function just lists all COMports that are available.
    Setting helpme to True will also print a help as to what comports are and 
    why we need them.
    '''
    logging.debug('Finding available Comports...')
    print("Available ports:")
    for i in serial.tools.list_ports.comports():
        print(i)
        logging.info('Comport found: %s' %str(i))
    if helpme:
        print("*******************HELP**********************")
        print("The PC has multiple ports to communicate with outside devices," 
              "such as USB ports, but also bluetooth. We must tell Python on "
              "which port is our machine. Because the temp-controllers use a"
              " 'serial RS232' port, and this computer only has usb-ports, we "
              "use a converter. Each PC has a different brand converter, so "
              "thats why I cant just select one automatically. The list just "
              "printed will contain a comport name (i.e., 'COM4', or "
              "'/dev/ttyUSB0', or something similar) and a description. The"
              "description tells you what is attached to the PC. In this case "
              "we are looking for somethin along the lines of 'USB-to-Serial "
              "converter'. Remember the corresponding COMport name, and input "
              "that into the regular script. And that's it. Easypeasy." )
        

class Temperature_controller():
    '''
    This is the superclass (metaclass). It cannot be used directly, but all 
    temperature controllers inherit from it. So, basically, if you change 
    something here, it will change something in all classes. Usefull for things 
    that all classes do, so for instance the ramping function.
    This Class has great power, use with great responsibility.
    '''
    def __init__(self,comport):
        self.comport = comport

    def __repr__(self):
        message = " <%s object controlling comport %s>" % (str(self.__class__),
                                                            self.comport)
        return message 
    
    def __str__(self):
        '''
        This is returned if you do print(Temperature_controller)
        '''
        message = "Connection to Temperature_controller at comport:\t%s\nInternal temperature is currently:\t%.2f\nSet temperature is currently:\t%.2f\n" % (self.comport,self._readtemp_internal(),self._readtemp_set())
        return message
    
    def _initialize_connection(self,
                               baudrate,
                               bytesize,
                               parity,
                               stopbits,
                               timeout=None,
                               xonxoff=False,
                               rtscts=False,
                               write_timeout=None,
                               dsrdtr=False,
                               inter_byte_timeout=None):
        '''
        Does what you think it does. It makes a connection to the waterbath with
        given parameters.
        '''
        logging.info('Initializing connection...')
        try: 
            connection = serial.Serial(
                self.comport,
                baudrate = baudrate,
                bytesize = bytesize,
                parity = parity,
                stopbits = stopbits,
                timeout = timeout,
                xonxoff = xonxoff, 
                rtscts = rtscts,
                write_timeout = write_timeout, 
                dsrdtr = dsrdtr,
                inter_byte_timeout = inter_byte_timeout,
                )
            logging.info('Connected to device at comport %s' % self.comport)
            return connection
        except serial.SerialException:
            logging.exception("Selected comport not found or wrong permissions.")
            raise serial.SerialException("Wrong comport, find the correct "
                                        "comport using"
                                        "'find_available_comports(True)'. If "
                                        "you are sure this is correct, see if "
                                        "you have permission to open COMports."
                                        " Or look for Piet.")
        
    def closecom(self):
        '''
        Close port if comport is open.
        '''
        if self.com.isOpen(): 
            logging.debug('Closing comport...')
            self.com.close()
            logging.debug('Comport is now closed')
            
    def opencom(self):
        '''
        Open port if comport is closed.
        '''
        if not self.com.isOpen():
            logging.debug("Opening comport...")
            self.com.open()
            logging.debug("Comport is now open")
            
    def _out_command(self,command,flush=True):
        '''
        Setting values of parameters. Does not return anything. Fot instance, 
        can set the temperature.
        
        Has error catching mechanism --> sometimes "SerialException: WriteFile 
        failed (PermissionError(13, 'The device does not recognize the command.',
        None, 22))" is thrown after long stretch of inactivity. Manually, you 
        can solve this by just restarting 'ju = julabo('com4')' etc.. 
        This is an attempt to do this automatically, so a ramp or something will
        not be disturbed.
        '''
        logging.debug("Trying to write command to device: '%s'" %str(command) )
        try:
            self.com.write( command.encode() )
            logging.debug("Command transfered to device succesfully")
        except serial.SerialException:
            logging.exception("Command transfer to device failed.")
            print("I detected that the connection to the device has been "
                "interupted. I will try to reset the connection. This may fail!")
            logging.info("Re-initializing connection after detecting broken connection")
            print(">>> REINITIALISING CONNECTION <<<")
            self.__init__(self.comport)
            self.com.write( command.encode() )
            logging.debug("Command transfered to device succesfully")
            print(">>>REINITIALISATION SUCCESFULL<<<")
        if flush:
            self._flush() # To remove command from buffer
        
    def _in_command(self,command):
        '''
        Asking for parameters or temperatures to be returned by waterbath. 
        Returns raw message.
        '''
        logging.debug("Trying to write command to device: '%s'" %str(command) )
        self._out_command(command,False) # use _out_command to send message
        time.sleep(0.1)
        readlength=self.com.inWaiting()
        message = self.com.read(readlength)
        logging.debug("Response received: '%s'" %str(message) )
        self._flush() # to remove command(and answer) from buffer
        return message
    
    def _flush(self):
        '''
        Flush the connection.
        '''
        logging.debug("Flushing connection")
        self.com.flushInput()
        self.com.flushOutput()
        
    def _readtemp_internal(self):
        '''
        This function is made to be overridden in one of the child classes. 
        Just to avoid errors in printing incomplete classes!
        '''
        return 0
    
    def _readtemp_external(self):
        '''
        This function is made to be overridden in one of the child classes. 
        Just to avoid errors in printing incomplete classes!
        '''
        return 0
    
    def _readtemp_set(self):
        '''
        This function is made to be overridden in one of the child classes. 
        Just to avoid errors in printing incomplete classes!
        '''
        return 0
    
    def _set_temperature(self,T):
        '''
        This function is made to be overridden in one of the child classes. 
        Just to avoid errors in printing incomplete classes!
        '''
        pass
    
    def passive_logging(self,time_interval = 15, verbose = False):
        '''
        Log the current internal temp/external temp/set temp every so often. 
        I will continue this until I get killed manually! 
        time_interval sets the time in seconds between each logging. 
        Minimum is quite low, 5 seconds is easily enough.
        set verbose to True to also print the found values (as opposed to 
        just logging them)
        '''
        print("Starting passive logging: I will note the temperatures every %f seconds. This will last indefinitly unless you kill me. To kill me, press crtl+c." % (time_interval,) )
        logging.debug("Start passive logging")
        while True:
            ti = time.perf_counter()
            Ti = self._readtemp_internal()
            Te = self._readtemp_external()
            Ts = self._readtemp_set()
            tolog = "T_internal = %s, T_external = %s, T_set = %s" % (str(Ti),str(Te),str(Ts)) 
            logging.info(tolog)
            if verbose:
                print(tolog)
                
            tf = time.perf_counter()
            # correct for time spent logging and stuff, make sure ctrl+c is possible and time.sleep does not lockup python.
            tcorrection = tf-ti
            slptime = math.floor(time_interval-tcorrection)
            if slptime <0:
                logging.error("passive_logging time_interval chosen too short")
                raise ValueError("time_interval too short! Passive logging impossible.")
            for _ in range(slptime):
                time.sleep(1)
            time.sleep(time_interval-tcorrection-slptime)
            
        
        
    def ramp(self,Tinit,Tend,dT,totaltime,ask=True,verbose=False):
        '''
        Makes a block temperature ramp with device for controlling temperature.

        IN:
            * Tinit     : Start temperature of ramp in deg C.
            * Tend      : Final temperature of ramp in deg C.
            * dT        : Temperature step of ramp in deg C.
            * totaltime : Total time of measurement in *seconds*.
            * ask       : Boolean, if True, will give all experimental info and 
                          wait for user conformation. If False, it will just 
                          start.
            * verbose   : Boolean, set to True to get all debug info.
        '''
        logging.info("You selected a ramp: Tinit=%f, Tend=%f, dT=%f, totaltime=%f" %(Tinit,Tend,dT,totaltime))
        t00 = time.perf_counter()                                             # Initialize internal clock (in seconds)
        steps = abs(round((Tend-Tinit)/dT))                       # Number of steps
        if Tinit > Tend: # Ramp down
            Trange = [round(Tinit - i*dT,2) for i in range(0,steps+1)] # Temperatures we will visit
        elif Tinit < Tend: # Ramp up
            Trange = [round(Tinit + i*dT,2) for i in range(0,steps+1)] # Temperatures we will visit
        else:
            raise ValueError('Detected problem with either Tinit or Tend value, they are probably equal.')
        logging.debug("Determined as Trange:'%s'" % str(Trange) )
        print('Temperature range is given by:\n'+str(Trange))
        waittime = totaltime / len(Trange)                         # Waiting time between steps in sec
        logging.debug("Time between temperature steps: %f" % (waittime,))
        fwaittime = str(datetime.timedelta(seconds=waittime))    # Formatted time for display
        ftotaltime = str(datetime.timedelta(seconds=totaltime))    # Idem dito
        
        print('The waiting time between each step is %s.' % (fwaittime,))
        if waittime <= 10:
            logging.warning("Ramp settings are chosen with short waiting times!")
            warnings.warn("The waiting step between 2 temperatures is probably to small for the waterbath to keep up. I suggest you try using a longer time.",)
        print('The total time of this ramp is %s.' % (ftotaltime,))
        
        if ask:
            test = input("Press enter to start ramp, press q to abort.")
            if 'q' in test:
                logging.info("Ramp aborted before start")
                raise ValueError("Aborted measurement before start.")
            else:
                pass
            
        t0=time.perf_counter()
        ft0 = str(datetime.timedelta(seconds=t0))
        
        if verbose:
            print('Starting at internal clock time: %s.' % (ft0,))
        
        logging.info("Starting ramp now")
        print('Starting ramp at:', datetime.datetime.now())
        
        for T in Trange:
            tnew = time.perf_counter()
            tbeforechange = time.perf_counter()
            if verbose:
                ftnew = str(datetime.timedelta(seconds=round(time.perf_counter())))
                print('Internal time - %s\t-\t Changing temperature to %.2f deg C...' % (ftnew,T))
                
            print(datetime.datetime.now().time(), "- Changing temperature to %.2f deg C..." % (T,))
            pasttime = int(round(tnew-t0))
            fpasttime = str(datetime.timedelta(seconds=pasttime))
            ftnew = str(datetime.timedelta(seconds=round(time.perf_counter())))
            
            if verbose:
                fpasttime = str(datetime.timedelta(seconds=pasttime))
                ftnew = str(datetime.timedelta(seconds=round(time.perf_counter())))
                print('Time past since last temperature change: %s.' % (fpasttime,))
                print('Internal time at changing Temperature - %s' % (ftnew,))
            
            self.changet(T)
            tafterchange = time.perf_counter()
            
            tcorrection = tafterchange-tbeforechange
            
            if verbose:
                print('time it took to change Temperature '+str(round(tcorrection)))
                print('time it took to change Temperature not rounded '+str(tcorrection))
            
            # This weird thing makes it possible to interrupt sleeping
            slptime = math.floor(waittime-tcorrection)
            for _ in range(slptime):
                time.sleep(1)
            time.sleep(waittime-tcorrection-slptime)
            
        ffinaltime = str(datetime.timedelta(seconds=round(time.perf_counter()-t00)))
        logging.info("Ramp finished without error!")
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
            * ask       : Boolean, if True, will give all experimental info and 
                          wait for user conformation. If False, it will just start.
            * verbose   : Boolean, set to True to get all debug info.
        '''
        steps = abs(round((Tend-Tinit)/dT))                 # Number of steps
        Trange = [round(Tinit + i*dT,2) for i in range(0,steps+1)] # Temperatures we will visit
        totaltime = len(Trange) * steptime
        self.ramp(Tinit,Tend,dT,totaltime,ask,verbose)
    
    def ramp_smooth(self,Tinit,Tend,totaltime,ask=True,verbose=False):
        '''
        Equivalent to ramp(), but with dT = 0.01 preset.
        Makes a continues temperature ramp (or as close to it as we can with our
        setup) with device for controlling temperature.

        IN:
            * Tinit     : Start temperature of ramp in deg C.
            * Tend      : Final temperature of ramp in deg C.
            * totaltime : Total time of the experiment in *seconds*.
            * ask       : Boolean, if True, will give all experimental info and 
                          wait for user conformation. If False, it will just 
                          start.
            * verbose   : Boolean, set to True to get all debug info.
        '''
        dT = 0.01
        self.ramp(Tinit,Tend,dT,totaltime,ask,verbose)
        
    def changet(self,temp):
        """
        Changes temperature of temperature control unit to temp, and checks if it was succesfull.
        Number will be rounded to 2 decimals. Also print current time because that can be useful.
        """
        temp = round(temp,2)     # In case somebody still puts in ##.###, note that ##.# or ## is no problem
        self.opencom()
        setcheck=False          # Sometimes setting the temp goes wrong and the first two digits are left out thats why we here check if the actual setpoint is the same as the desired setpoint, or sometimes the whole communication fails with rs232 port 
        i=0
        while setcheck==False:
            i=i+1
            logging.debug("Attempt to change temperature to %f using changet() function" % temp)
            self._set_temperature(temp)
            time.sleep(1)
            try:                                         # In case reading data leads to error, disconnect and reconnect (sometimes happens with Julabo)
                settemp = self._readtemp_set()
                setcheck = (settemp==temp or settemp == 0 )    # If settemp is '0', it is unimplemented for whatever reason and we continue without checking.
                if not setcheck:                         # If temperature was not set correctly, throw an error and handle together with 'real' errors
                    raise serial.SerialException("the wrong temperature was set")
            except Exception as e:
                ex = str(e)
                logging.error(ex)
            if not setcheck:
                if i > 3:
                    logging.warning("Datatransfer failed %i times in a row" % i)
                    warnings.warn("Datatransfer failed %i times in a row, try diconnecting and reconnecting the USB cable. I will not throw a real error, because sometimes feedback of machine doesn't work, while temperature is changed corretly." % (i,) )
                    break
                logging.warning("Something went wrong in datatransfer: '%s'. Try setting temperature again." % (ex, ))
                print("Something went wrong in datatransfer: '%s'.\nTrying again." % (ex, ))
                self.closecom() # close com and open again to try and restore data connection
                time.sleep(2)
                self.opencom()
                            
        #self.closecom()
        if i>1 and setcheck==True:
            print("Recovered from error(s) succesfully.")
        logging.debug("Temperature set correctly")
        logging.info("Temperature set to %.2f deg C." % (temp,))
        # Print confirmation of temperature setting, and current time because usefull.
        print(datetime.datetime.now().time(),"- Temperature set to %.2f deg C." % (temp,) )


class Lauda(Temperature_controller):
    '''
    DO NOT USE DIRECTLY, USE FOR INSTANCE 'LaudaE200'!
    This is the metaclass from which all Lauda watherbaths can inherit - since 
    the raw commands are the same anyway.
    If you change/add a function here, it changes for all Haake waterbaths.
    '''
    def __init__(self,comport):
        super().__init__(comport)
        self.errors = {
            "ERR_2" : "Wrong input (e.g. buffer overflow)",
            "ERR_3" : "Wrong command",
            "ERR_5" : "Syntax Error in value",
            "ERR_6" : "Illegal Value",
            "ERR_8" : "Channel (like external temperature) not available",
            "Err_30": "Programmer, all segements occupied",
        }
    
    def am_I_in_control(self):
        '''
        Check if the programming interface is in control
        TODO: This throws an error!
        '''
        logging.debug("Reading whether I can control the Lauda via the programming interface")
        type_command = "IN MODE 01\r"
        message = self._in_command(type_command)
        logging.debug("Raw return of control request is: '%s'" % str(message))
        return bool(self._lauda_message_handler(message))
    
    def type(self):
        '''
        Print thermostat type
        '''
        logging.debug("Reading Lauda thermostat type")
        type_command = "TYPE\r"
        message = self._in_command(type_command)
        logging.debug("Raw type return is: '%s'" % str(message))
        return message
    
    def version(self):
        '''
        Print software version
        '''
        logging.debug("Reading Lauda thermostat software version")
        version_command = "VERSION\r"
        message = self._in_command(version_command)
        logging.debug("Raw version return is: '%s'" % str(message))
        return message
        
    def _readtemp_internal(self):
        '''
        Reads out internal temperature.
        '''
        logging.debug("Reading internal temperature")
        readtemp_I_command = "IN PV 00\r"
        message = self._in_command(readtemp_I_command)
        logging.debug("Internal temperature reading is: '%s'" % str(message))
        return self._lauda_message_handler(message) # Which is temperature parsed from output
        
    def _readtemp_external(self):
        '''
        Reads out external temperature. Usefull if we add sensor to setup 
        (which we won't do, but you know...).
        '''
        logging.debug("Reading external temperature")
        readtemp_E_command = "IN PV 01\r"
        message = self._in_command(readtemp_E_command)
        logging.debug("External temperature reading is: '%s'" % str(message))
        try:
            t = self._lauda_message_handler(message) # temperature parsed from output
        except Exception:
            t = -1000 # prevent errors in inhereting stuff.
        return t 
    
    def _readtemp_set(self):
        '''
        Reads out set temperature.
        '''
        logging.debug("Reading set temperature")
        readtemp_S_command = "IN SP 00\r"
        message = self._in_command(readtemp_S_command)
        logging.debug("Set temperature reading is: '%s'" % str(message))
        return self._lauda_message_handler(message) # Which is temperature parsed from output
    
    def _set_temperature(self,temperature):
        '''
        Changes set temperature of waterbath. DO NOT USE DIRECTLY.
        '''
        logging.debug("Changing set temperature to '%s'" % str(temperature) )
        settemp_command = "OUT SP 00 {0:06.2f}\r".format(float(temperature))
        self._out_command( settemp_command )
        logging.debug("Set temperature was changed")
    
    def set_pumppower(self, power):
        '''
        Sets power of pump to 1,2,3,4, or 5. Turning it off via this way is NOT suported
        '''
        power = round(power)
        if not (0 < power <= 5):
            raise ValueError("Pumppower must be between 1 and 5")
        logging.debug("Changing power of pump to '%i'" % (power,) )
        settemp_command = "OUT SP 01 {0:03}\r".format(power)
        self._out_command( settemp_command )
        logging.debug("Pump power was changed")
        
    def _lauda_message_handler(self,message):
        '''
        Parses what the Lauda returns into a readable temperature.
        The Lauda returns something like b'023.45' or b'-015.60' which equals +23.45 and -15.6 degree C. Also possible are errors, like "ERR_2". If you give a command, it will also say OK, meaning there are 2 messages waiting for you, like: b'OK\r\n 033.50\r\n'. We handle that by just only returning the last thing in the list of things you said. Which can be done more elegantly, but this will work in like 99% of cases so why bother.
        '''
        # print(message) # For debug
        # cut off all carriage return (\r) and line feed (\n) commands
        if type(message) == bytes:
            message = message.decode()
        elif type(message) != str:
            raise TypeError("can only parse string and byte objects, but given type was {0}!".format(type(message)))
        messages = message.split() # often there is more then one waiting message. This will also clean any \r\n stuff.
        # only return the last number, probably you are not interested in OK (and ERROR allready gives an error!)
        parsed = list()
        for m in messages:
            parsed.append( self._lauda_parser(m) )
        return parsed[-1]
    
    def _lauda_parser(self,message):
        """
        See _lauda_message_handler() for full docs.
        I require a str as message input here! 
        """
        assert type(message) == str
        message = message.replace('\r\n', '') # just to be sure
        try:
            return float(message)
        except ValueError:
            # This means the machine says "OK", or there is some error.
            try:
                if message == "OK":
                    return message
                errormessage = message + " : " + self.errors[message]
                raise ValueError(errormessage)
            except KeyError:
                #print(e) #For debug
                raise ValueError("Parser could not read Lauda response: '%s'" % (str(message),))
            
    def start_pump(self):
        logging.info("Starting pump and heating/cooling")
        startpump_command = "START\r"
        self._out_command( startpump_command )
        
    def stop_pump(self):
        logging.info("Stopping pump and heating/cooling")
        stoppump_command = "STOP\r"
        self._out_command( stoppump_command )

class LaudaE200(Lauda):
    '''
    Class for controlling the Lauda Ecoline E200 waterbath.
    Inherits from Lauda superclass. Look there for the functions you might need.
    '''
    
    def __init__(self,comport):
        logging.info("You selected the Lauda Ecoline E200 Waterbath")
        super().__init__(comport)
        self.com = self._initialize_connection(
            baudrate = 9600, # can be set manually in the machine!    
            bytesize = serial.EIGHTBITS,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            timeout = 15,
            xonxoff = False,
            rtscts = True, # set to false if it soes not work!
            write_timeout = 15,
            dsrdtr = False,
            inter_byte_timeout = None
            )
        self.opencom()

class haake(Temperature_controller):
    '''
    DO NOT USE DIRECTLY, USE FOR INSTANCE 'haakeF6' OR 'haakePhoenix'!
    This is the metaclass from which all Haake watherbaths can inherit - since 
    the raw commands are the same anyway.
    If you change/add a function here, it changes for all Haake waterbaths.
    '''
    def __init__(self,comport):
        super().__init__(comport)
    
    def _readtemp_internal(self):
        '''
        Reads out internal temperature.
        '''
        logging.debug("Reading internal temperature")
        readtemp_I_command = "F1\r"
        message = self._in_command(readtemp_I_command)
        logging.debug("Internal temperature reading is: '%s'" % str(message))
        return self._haake_temp_parser(message) # Which is temperature parsed from output
        
    def _readtemp_external(self):
        '''
        Reads out external temperature. Usefull if we add sensor to setup 
        (which we won't do, but you know...).
        '''
        logging.debug("Reading external temperature")
        readtemp_E_command = "F2\r"
        message = self._in_command(readtemp_E_command)
        logging.debug("External temperature reading is: '%s'" % str(message))
        return self._haake_temp_parser(message) # Which is temperature parsed from output
    
    def _readtemp_set(self):
        '''
        Reads out set temperature.
        '''
        logging.debug("Reading set temperature")
        readtemp_S_command = "R SW\r"
        message = self._in_command(readtemp_S_command)
        logging.debug("Set temperature reading is: '%s'" % str(message))
        return self._haake_temp_parser(message) # Which is temperature parsed from output
    
    def _set_temperature(self,temperature):
        '''
        Changes set temperature of waterbath. DO NOT USE DIRECTLY, 
        USE haakeF6.changet() INSTEAD!
        '''
        logging.debug("Changing set temperature to '%s'" % str(temperature) )
        settemp_command = "S  %i\r" % (round(float(temperature) * 100),)
        self._out_command( settemp_command )
        logging.debug("Set temperature was changed")
        
    def _haake_temp_parser(self,message):
        '''
        Parses what the Haake returns into a readable temperature.
        The Haake returns something like b'$\r\nSW+033.99$\r\n' which equals 
        +33.99 degree C.
        '''
        #print(message) #For debug
        try:
            return float(message[2:9])
        except ValueError:
            # Sorta quick hack: Sometimes, return format is different (it adds leading '$\r\n' for reasons I did not look into), so try other extraction type
            try:
                return float(message[5:12])
            # If it still doesn't work, give detailed error response.
            except Exception:
                #print(e) #For debug
                raise ValueError("Parser could not read haake response: '%s'" % (str(message),))

    def read_RTA_internal(self):
        '''
        Reads the internal temperature correction factor c.
        '''
        logging.debug("Reading internal RTA values (for temperature correction)")
        readRTA_I_command = "R CI\r"
        message = self._in_command( readRTA_I_command )
        c = self._haake_temp_parser( message )
        time.sleep(1)
        self._flush()
        logging.debug("Internal RTA factor raw is '%s'" % str(message) )
        logging.info("Internal RTA factor, c = %s" % str(c))
        return c,message
    
    def set_RTA_internal(self,setc):
        '''
        WARNING. THIS CHANGES THE CORRECTION FACTOR 'C', LEADING TO A 
        DIFFERENT INTERNAL TEMPERATURE.
        NEVER CHANGE THIS IF YOU DO NOT NOW WHAT YOU ARE DOING!
        In case you screw up, +0.50 seems to be a sort of okay value.
        '''
        logging.warning("I am about to set the internal RTA value to %s!" % str(setc) )
        setRTA_I_command = "W CI %.2f\r" % (setc,)
        self._out_command( setRTA_I_command )
         
    def start_pump(self):
        logging.info("Starting pump and heating/cooling")
        startpump_command = "GO\r"
        self._out_command( startpump_command )
        
    def stop_pump(self):
        logging.info("Stopping pump and heating/cooling")
        stoppump_command = "ST\r"
        self._out_command( stoppump_command )
    
    def alarm(self):
        logging.warning("Sending the signal to raise the alarm via dataconnection!")
        alarm_command = "AL\r"
        self._out_command( alarm_command )
        
    def alarm_stop(self):
        logging.warning("Stopped alarm via dataconnection!")
        alarm_stop_command = "ER\r"
        self._out_command( alarm_stop_command )
    
class haakeF6(haake):
    '''
    Class for controlling HaakeF6 waterbath.
    Inherits from haake superclass. Look there for the functions you might need.
    '''
    
    def __init__(self,comport):
        logging.info("You selected the Haake F6 Waterbath")
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
    Changing the temperature correction factor is not functional for unknown 
    reasons, the rest works fine.
    
    Note that temperature given by the bath is of by about +0.8 degree C. 
    (we cant correct internally due to weird non-functional RTA).
    Always start by starting the pump using haakePhoenix.start_pump(), 
    as it does not start automatically.
    '''
    def __init__(self,comport):
        logging.info("You selected the Haake Phoenix Waterbath")
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
    (If we ever get another Julabo waterbath, we can convert this to a metaclass
    like 'haake')
    '''
    
    def __init__(self,comport):
        logging.info("You selected the Julabo Waterbath")
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
        logging.debug("Now parsing the temperature from raw output, '%s'" % str(message) )
        message_cleaned = str(message[0:-2])
        message_cleaned2 = message_cleaned.replace("\\xb","")
        message_cleaned3 = message_cleaned2[2:7]
        logging.debug("Temperature was parsed to '%s'" % str(message_cleaned3) )
        if '---' in message_cleaned3: # in this case, there is no sensor to read from, just return 0.
            floated_message = 0.00
        else:
            floated_message = float(message_cleaned3)
        return floated_message
        
        
    def _set_temperature(self,temperature):
        '''
        Changes set temperature of waterbath to 'temperature'. 
        DO NOT USE DIRECTLY, USE changet() INSTEAD!
        '''
        logging.debug("Setting temperature to %s" % str(temperature) )
        settemp_command = "out_sp_00 %06.2f\r" % (float(temperature),)
        self._out_command( settemp_command )
            
    def status(self):
        '''
        Reads any messages or error codes from the machine.
        '''
        logging.debug("Reading current status of device")
        readtemp_I_command = "in_pv_00\r"
        message = self._in_command( readtemp_I_command )
        logging.info("current status of device: %s" % str(message) )
        print(message)
    
    def _readtemp_set(self):
        '''
        Reads out set temperature.
        '''
        logging.debug("Reading set temperature")
        readtemp_S_command = "in_sp_00\r"
        message = self._in_command( readtemp_S_command )
        settemp = self._julabo_temp_parser(message)
        logging.debug("Set temperature reading is: '%s'" % str(settemp))
        return settemp
    
    def _readtemp_internal(self):
        '''
        Reads out internal temperature.
        '''
        logging.debug("Reading internal temperature")
        readtemp_I_command = "in_pv_00\r"
        message = self._in_command( readtemp_I_command )
        temp = self._julabo_temp_parser(message)
        logging.debug("Internal temperature reading is: '%s'" % str(temp))
        return temp
    
    def _readtemp_external(self):
        logging.debug("Reading external temperature")
        readtemp_E_command = "in_pv_02\r"
        message = self._in_command( readtemp_E_command )
        temp = self._julabo_temp_parser(message)
        logging.debug("External temperature reading is: '%s'" % str(temp))
        return temp

    def start_pump(self):
        '''
        Starts the pump and heating/cooling elements of this waterbath.
        '''
        logging.info("Starting pump and heating/cooling")
        start_P_command = "out_mode_05 1\r"
        self._out_command( start_P_command )
        
    def stop_pump(self):
        '''
        Stops the pump and heating/cooling elements of this waterbath.
        '''
        logging.info("Stoppinh pump and heating/cooling")
        stop_P_command = "out_mode_05 0\r"
        self._out_command( stop_P_command )
        
    def wiggle(self,temp,time=120):
        '''
        This is a TEMPORARY hack, to make sure Julabo stays connected to slow 
        confocal. Works by changing T every 'time' seconds and almost immediatly 
        changing it back.
        Just use "ctrl + c" to stop this, it runs ad infinitem.
        '''
        logging.info("I started the 'wiggle' script. There will be NO log when it stops!")
        while True:
            self.changet(temp+0.01)
            time.sleep(2)
            self.changet(temp)
            for _ in time:
                time.sleep(1)
        
class electric(Temperature_controller):
    '''
    Class for controlling the electric peltier-element-based heater.
    Note that we can control the temperature of the three components seperatly by
    calling electric.set_temperature_controller(temp,[2,3]). The self.changet 
    and ramp function assume we want to ramp all three components at the same 
    speed at the same temperature.
    WARNING: There is no feedback system in place yet to test whether data 
    transfer is succesfull in the electric control unit. Thread carfully.
    '''
    def __init__(self,comport):
        logging.info("You selected the electric temperature controller")
        logging.warning("The electric temperature controller has no logging functionality (yet)")
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
        self._set_temperature(22.22)
        
    def _datagenelec(self, temp, controller): #
        '''
        Generates data for command to electric control unit.
        enter temp as float (##.## - 2 decimals) and controllor as integer - 1,2 or 3.
        '''
        stx=b'\x02'
        etx=b'\x03'
        subadress=b'00'
        SID=b'0'

        controllerbit=('0'+str(controller)).encode('UTF-8')    # either 01,02,03
        command=b'0102C4000000000100000'                    # for changing the set point of the first bank, which is what you want
        temp=int(round(temp*100))                      #rounding 
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
        logging.info("You selected the Thermo Fischer Waterbath")
        logging.warning("The Thermo has no logging functionality, and is really in the testing phase!")
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


if __name__ == "__main__":
    # Initialize logging. Logging is usefull, because I can see back when I changed temperatures and stuff like that.
    logginglevel =  logging.INFO # Set to debug if you want to go debugging. Otherwise, leave at info, so we can use the logfile to see what we did in the past.
    logging.basicConfig(filename='tempcontroller_info.log', level=logginglevel, format='%(asctime)s - %(levelname)s: %(message)s')
    logging.info('New session was started')

    # This checks if you are using a Windows XP machine, and if so, gives a small lecture about the dangers of Windows XP and serialports.
    if 'win' in sys.platform:
        logging.debug('Windows platform detected')
        try:
            wv = sys.getwindowsversion()
            if wv.major <= 5: # If using windows 5 (WINDOWS XP) or below, give a warning
                logging.warning('Windows XP detected - connection probably unstable!')
                print("*****I DETECT WINDOWS XP*****")
                time.sleep(1)
                warnings.warn("The serial ports have the tendency to loose connection when connected for extended periods of time without commands comming in on this version of Windows. Therefore, I advise using the 'wiggle' function as an alternative to 'changet'. This wiggles the temperature by 0.01 degrees every 2 minutes. This way, connection will not be lost and you will be safe!")
                time.sleep(1)
                print("*****END OF SAFETY MESSAGE*****")
        except:
            pass
    
    find_available_comports()
