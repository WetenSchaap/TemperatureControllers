import serial
import csv
import time
import sys


#csv_file = "test.csv" 

def setcomport(comportname):
    """sometimes it is three sometimes 4"""    
    global __comport__
    __comport__=comportname    

def opencomglobalhaake(comportname):
    global __com__
    try: 
        __com__ = serial.Serial(comportname,9600,bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
    except serial.SerialException:
        raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc)')

def opencomglobalthermo(comportname):
	global __com__
	try:
		__com__ = serial.Serial(comportname,9600,bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
	except serial.SerialException:
        raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc)')
		
def opencomglobaljulabo(comportname):
    global __com__
	
	try:
		__com__ = serial.Serial(comportname,4800,bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,timeout=1, xonxoff=0,rtscts=0)
	except serial.SerialException:
        raise serial.SerialException('Wrong comport, find the correct comport in Device Manager (run-->devmgmt.msc)')
		
def startjulabo():
    __com__.close()
    __com__.open() 
    __com__.write("out_mode_05 1\r".encode())
    
    
def closecom():
    __com__.close()
    
def changethaake(temp):
    """
    temp should be of form ##.##
    """
#    try:
#      com
#    except NameError:
 #       com = None
 #  if com != None: com.close()
  #  com = serial.Serial(__comport__,4800,bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
    temp=round(temp,2) #in case somebody still puts in ##.###, note that ##.# or ## is no problem
    if (__com__.isOpen() == False): __com__.open()  #open is comport is closed
  
    setcheck=False #sometimes setting the temp goes wrong and the first two digits are left out thats why we here check if the actual setpoint is the same as the desired setpoint
    #or sometimes the whole communication fails with rs232 port 
    i=0
    while setcheck==False:
        i=i+1
        __com__.flushInput()
        __com__.flushOutput()        
        settemp_command = "S  " + str(int(round(float(temp) * 100)))+"\r"
        __com__.write( settemp_command.encode() )
        time.sleep(1)
        __com__.flushInput()
        __com__.flushOutput()
        __com__.write("S\r".encode()) 
        time.sleep(1)
        readlength=__com__.inWaiting()
        #print(readlength)
        setcheck=(readlength==12)   #if you ask for "S\r" phoenix should return a 12 byte long expression of form b"+0037.00 C$\r" (\r is one ascii caracter meaning CR)
        if setcheck==False:
			if i > 10:
				raise serial.SerialException( 'Datatransfer failed %i times in a row, check connection.' % (i,) )
            print("something went wrong in datatransfer, try again")
            __com__.close() #close com and open again to restore data connection
            time.sleep(1)
            __com__.open()
        else: #only continue if data transfer went ok
            message=__com__.read(readlength)
            print(message)
            settemp=float(message[3:8])
            print(settemp)
            setcheck=(temp==settemp)
            if setcheck==False:
                print("the wrong temperature was set, will try again")
    __com__.close()
    print(i)

def changetthermo(temp):
    """
    temp should be of form ##.##
    """
#    try:
#      com
#    except NameError:
 #       com = None
 #  if com != None: com.close()
  #  com = serial.Serial(__comport__,4800,bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
    __com__.close()
    __com__.open()    
    setcheck=False #sometimes setting the temp goes wrong and the first two digits are left out thats why we here check if the actual setpoint is the same as the desired setpoint
    i=0
    while setcheck==False:
        i=i+1
        __com__.flushInput()
        __com__.flushOutput()        
        settemp_command = "SS " + str(temp)+"\r"
        __com__.write( settemp_command.encode() )
        time.sleep(1)
        __com__.flushInput()
        __com__.flushOutput()
        __com__.write("RS\r".encode()) 
        time.sleep(1)
        readlength=__com__.inWaiting()
        #print(readlength)
        message=__com__.read(readlength)
        #print(message)
        settemp=float(message[3:8])
        #print(settemp)
        setcheck=(temp==settemp)
        if setcheck==False:
			if i > 10:
				raise serial.SerialException( 'Datatransfer failed %i times in a row, check connection.' % (i,) )
            print("the wrong temperature was set, will try again")
    __com__.close()
    print(i)
    
def changetjulabo(temp):
    """
    temp should be of form ##.##
    """
#    try:
#      com
#    except NameError:
 #       com = None
 #  if com != None: com.close()
  #  com = serial.Serial(__comport__,4800,bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
    __com__.close()
    time.sleep(1)
    __com__.open()    
    time.sleep(1)
    settemp_command = "out_sp_00 0" + str(temp)+"\r"
    __com__.write( settemp_command.encode() )

    if (__com__.isOpen() == False): __com__.open()  ##open is comport is closed
  
    setcheck=False ##sometimes setting the temp goes wrong and the first two digits are left out thats why we here check if the actual setpoint is the same as the desired setpoint
    ##or sometimes the whole communication fails with rs232 port 
    i=0
    while setcheck==False:
        if i>10:
			raise serial.SerialException( 'Datatransfer failed %i times in a row, check connection.' % (i,) )
        i=i+1
        __com__.flushInput()
        __com__.flushOutput()        
        settemp_command = "out_sp_00 0" + str(temp)+"\r"
        __com__.write( settemp_command.encode() )
        time.sleep(1)
        __com__.flushInput()
        __com__.flushOutput()
        __com__.write("in_sp_00\r".encode())
        time.sleep(1)
        readlength=__com__.inWaiting()
        #print(readlength)          # usefull for debug
        setcheck=(readlength==7)   ##in_sp_00\r julabo will give the setpoint in a bit unclear encoding but i managed some hacked way to get the temp
        if setcheck==False:
            print("something went wrong in datatransfer, try again")
            __com__.close() ##close com and open again to restore data connection
            time.sleep(1)
            __com__.open()
        else: ##only continue if data transfer went ok
            message=__com__.read(readlength)
            #print(message)         # usefull in debug
            message_cleaned=str(message[0:-2])
            message_cleaned2=message_cleaned.replace("\\xb","")
            message_cleaned3=message_cleaned2[2:7]
            settemp=float(message_cleaned3)
            print('temperature set to %s deg C' % (settemp,))
            setcheck=(temp==settemp)
            if setcheck==False:     
                print("the Julabo reports the wrong temperature, will try again")
    __com__.close()
    #print(i)       #number of tries - for debug
    
def ramphaake(Tinit,Tend,dT,totaltime):
    t00=time.clock()
    steps=int(round((Tend-Tinit)/dT))
    Trange=[round(Tinit + i*dT,2) for i in range(0,steps+1)]
    print('Trange is given by '+str(Trange))
    waittime=totaltime/len(Trange) 
    print('Waiting time between each step is '+str(waittime))
    t0=time.clock()
    print('starting at time '+str(int(round(t0))))
    for T in Trange:
        tnew=time.clock()
        print('changing temp at time '+str(int(round(tnew))))
        print('difference in time before last change '+str(int(round(tnew-t0))))
        print('difference in time before last change not rounded '+str(tnew-t0))
        t0=tnew
        changethaake(T)
        tafterchange=time.clock()
        tcorrection=tafterchange-t0
        print('time it took to change sp '+str(int(round(tcorrection))))
        print('time it took to change sp not trounded '+str(tcorrection))
        print('wait time till next temperature '+str(waittime-tcorrection))
        time.sleep(abs(waittime-tcorrection)) ##otherwise the totaltime of the ramp is not totaltime but total+#ofTs*tcorrection
        ##if tcorrection is bigger than waittime we would have to wait negative times to end up with ttotal, we make it an absolute value to not get an error, however ttotal will not be exact anymore
    print('total time it really took '+ str(time.clock()-t00))
 
def rampjulabo(Tinit,Tend,dT,totaltime):
    t00=time.clock()
    steps=int(round((Tend-Tinit)/dT))
    Trange=[round(Tinit + i*dT,2) for i in range(0,steps+1)]
    print('T_range is given by '+str(Trange))
    waittime=totaltime/len(Trange) 
    print('Waiting time between each step is '+str(waittime) + ' seconds')
    t0=time.clock()
    print('starting at time '+str(int(round(t0))))
    for T in Trange:
        tnew=time.clock()
        print('changing temp at time '+str(int(round(tnew))))
        print('difference in time before last change '+str(int(round(tnew-t0))))
        #print('difference in time before last change not rounded '+str(tnew-t0))
        t0=tnew
        changetjulabo(T)
        tafterchange=time.clock()
        tcorrection=tafterchange-t0
        print('time it took to change sp '+str(int(round(tcorrection))))
        #print('time it took to change sp not trounded '+str(tcorrection))
        print('wait time till next temperature '+str(waittime-tcorrection))
        time.sleep(abs(waittime-tcorrection)) ##otherwise the totaltime of the ramp is not totaltime but total+#ofTs*tcorrection
        ##if tcorrection is bigger than waittime we would have to wait negative times to end up with ttotal, we make it an absolute value to not get an error, however ttotal will not be exact anymore
    print('total time it really took '+ str(time.clock()-t00))
    
def loophaake(loopnmb,Thigh,Tlow,Thigh_time,Tlow_time):
    

    for i in range(loopnmb):
        changethaake(Thigh)
        time.sleep(Thigh_time)
        changethaake(Tlow)
        time.sleep(Tlow_time)
        
def bcccalcelec(data):
    bcc=ord(chr(data[1]))
    for i in range(2,len(data)):
        bcc=bcc ^ ord(chr(data[i]))  
    return chr(bcc).encode('UTF-8')

def datagenelec(temp, controller): #enter temp as float st ##.## and controllor as int 1,2 or 3

    stx=b'\x02'
    etx=b'\x03'
    subadress=b'00'
    SID=b'0'

    controllerbit=('0'+str(controller)).encode('UTF-8') #either 01,02,03
    command=b'0102C4000000000100000' #for changing the set point of the first bank, which is what you want
    temp=int(round(temp*100)) #rounding 
    hexnmb=hex(temp)[2:].upper().encode('UTF-8')
    data=stx+controllerbit+subadress+SID+command+hexnmb+etx
    databcc=data+bcccalcelec(data)
    return databcc

def changetelec(temp, controller):
    ser = serial.Serial(__comport__, 9600, bytesize=7, parity=serial.PARITY_EVEN, stopbits=2, xonxoff=0, rtscts=0, timeout=1)
    data=datagenelec(temp,controller)
    ser.close()
    ser.open()
    ser.write(data)
    #print(ser.read(40))
	
def changetelec_all(temp):
	changetelec(temp, 1)
	changetelec(temp, 2)
	changetelec(temp, 3)
	print("Temperature set to %f deg C")
	
    
def rampelec(Tinit,Tend,dT,totaltime):
	'''
	Makes a tempramp with the electronically controlled temperature unit. Temperatures in deg C and totaltime in *SECONDS*
	There is no feedback control for this unit, so you should check if stuff really works!
	'''
	
    t00=time.clock()
    steps=int(round((Tend-Tinit)/dT))
    Trange=[round(Tinit + i*dT,2) for i in range(0,steps+1)]
	
    print('Temperature range is given by:\n'+str(Trange))
	
    waittime=totaltime/len(Trange) 
	waittimemin = waittime/60
	
    print('The waiting time between each step is %f minutes' % (waittimemin,))
	
    t0=time.clock()
	
    print('starting at time '+str(int(round(t0))))
	
    for T in Trange:
        tnew=time.clock()
        print('Changing temp at time: '+str(int(round(tnew))))
		pasttime = int(round(tnew-t0))/60
        print( 'Time past since last change: %f minutes' % (pasttime,) )
        #print('difference in time before last change not rounded '+str(tnew-t0))
        t0=tnew
        changetelec_all(T)        
        tafterchange=time.clock()
        tcorrection=tafterchange-t0
        #print('time it took to change sp '+str(int(round(tafterchange-t0))))
        #print('time it took to change sp not trounded '+str(tafterchange-t0))
        time.sleep(waittime-tcorrection)
    print('Total time it really took '+ str(time.clock()-t00))