#!/usr/bin/env python

import sys
import time
import datetime
import subprocess
import string

#import LabPython U3 function
import u3



# This routine is used for logging events of a Paravision
#	It is initiated by calling ./captureTriggers.py from a PV terminal window.  No other input is needed.
#	It runs continuously, so interrupting with Control-C is the only way to stop it.
#
#
#  It is to be used with a LabJack U3 device to convert TTL (ECG) stamps from a
#  running scan to a USB interface on the scanner console computer.
#  The labjack python functions repeatedly monitor the device, but if the device is not present it uses
#  a simple timer for debugging all of the other capabilities.
#  This script monitors the status of Paravision and begins logging when a scan starts,
#  and tests whether the scan is in the "Scanning" or "Reco" states as opposed to the Adjust or Scheduled state.
#  
#  With the fully functional U3 in place, this file, run from the PV terminal window (no arguments needed),
#  will monitor PV for a new scan with triggerout implemented and will begin logging to a text file in the 
# experiment directory.  Each time a trigger (ECG HIGH to LOW) is found, it will record the time since the scan
# started and the elapsed time since the trigger.  No other user input is needed, although it has not been fully tested.
#  12/10/18 Matt Budde, MCW
#
# Technical details:
# The script uses 'pvcmd' calls to evaluate the current state of Paravision, and if a scan is started/running, will 
# initiate the logger.  The logging is called from a separate thread, so it can continue while the main program continues
# to check the PV state. 
# Some error checking is implemented to check if the pvcmd call works or if the U3 is connected. 





class Param:
    def __init__(self):
        self.deviceU3 = None
        self.isU3 = False


def openandConfigureU3(u3Debugstate):
	print("Trying to open LabJack U3 device.\n")
	param.isU3 = False
	try:
		param.deviceU3 = u3.U3()  # Opens first found U3 over USB
	
		if isinstance(param.deviceU3, u3.U3):
	     		param.deviceU3.debug = u3Debugstate
			param.deviceU3.configIO(EnableCounter0 = True, FIOAnalog = 15)
			param.isU3 = True
			print("LabJack U3 device Enabled.\n")
			
	except:
		param.isU3 = False

	return param.isU3



def LogU3(sleeptime):

	# for each timepoint ~1 ms??
	#if changed, log the timestamp
	#read the TTL status

	starttime=time.time()
	ptime = starttime
	ncnt = 0
	print("Monitoring Counter0.\n")

	while 1:
		time.sleep(sleeptime)
		#readU3()
		if param.isU3==True:	
	  		#bitState=d.getFeedback(u3.BitStateRead(IONumber = 5))
			bitState=param.deviceU3.getFeedback(u3.Counter0(Reset = True))
		else:
			bitState=1
			time.sleep(sleeptime*100)

		#the state of the BitStateRead will use high/low.  The PV pulse sequences are programmed to low on trigger since the U3 counter advances on the low state. 
		#  The labjack forums for this particular purpose state that if the pulse duration is 10ms or so, reading directly the state will be appropriate.  I believe this can be achieved in the Paravision sequences for certain applications, but not all.  The alternative it to use the digital counter, which can be read faster.  This is currently implemented here.	
		if (bitState[0]>0):
		
			ntime=time.time()
			#this will cause a delay, but it's better to use here than for each check to avoid overheads.			
			nowtime=(ntime - starttime)*1000.0
			elapsed=(ntime - ptime)*1000.0
			deltams=str("%.02f" % elapsed )
			elapsedms=str("%.02f" % nowtime )
			rowstring=str(ncnt)+"\t"+str(bitState[0])+"\t"+elapsedms+"\t"+deltams+"\n"
	
			print(rowstring)
			ncnt=ncnt+1
			ptime=ntime
	



#=======================================================================================================================
# Start program
#=======================================================================================================================
if __name__ == "__main__":

	param = Param()

	Monsleeptime= 1 #in seconds for monitoring running scan
	Logsleeptime= 0.001 #in seconds for checking/logging triggers
	u3Debugstate = False
	
	if openandConfigureU3(u3Debugstate)==False:
		print "U3 not loaded or configured.\n  Doing logging with sleep timer."
	 


	newscan=0
	triggBool=0

	prevDset=""
	LogU3(Logsleeptime)

