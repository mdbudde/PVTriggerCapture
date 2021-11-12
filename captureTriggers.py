#!/usr/bin/env python

import sys
import time
import datetime
import subprocess
import string
from multiprocessing import Process

import BrukerMRI as bruker

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
# experiment directory.  Each time a trigger (TTL HIGH to LOW) is found, it will record the time since the scan
# started and the elapsed time since the trigger.
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


#def readU3():
#	# Reading Digital I/O
#	print("\nDigital I/O:\n")
#	for i in range(4):
#		dirRegister = 6100 + i  # Starting register 6100, 1 register at a time
#		stateRegister = 6000 + i  # Starting register 6000, 1 register at a time
#		fio = i
#	if isU3:
#		fio = i+4
#		dirRegister = 6100 + 4 + i
#		stateRegister = 6000 + 4 + i
#
#	print("FIO%s (register %s) Direction: %s" % (fio, dirRegister, param.deviceU3.readRegister(dirRegister)))
#
#	state = param.deviceU3.readRegister(stateRegister)
#	print("FIO%s (register %s) State: %s" % (fio, stateRegister, state))
#	if state == 0:
#		state = 1
#		wordState = "high"
#	else:
#		state = 0
#		wordState = "low"
#	return state


def loadBruker(methopath):

	#read parameters
	pvParams=bruker.ReadParamFile(methodPath)
	#for key,val in pvParams.items():
	#	print key, ": ", val
	return pvParams



def CaptureAndWriteLog(fd,sleeptime):

    alivestatecycles = 10000 #number of cycles to check on the device status.  Each cycle is sleeptime in duration.
    alivestatecnt = 0 #increment for checking the device status.
    ncnt=0
	ptime=time.time() #get time at the start of this loop, ptime will also get updated for each event
	starttime=ptime
	prevBitState=0
	bitState = 0  #this is the counter in the U3 device.  If > 0, an event has occurred (TTL2_LOW)

    #reconfigure the device before we start with the repeated looping/monitoring
    CounterConfig = param.deviceU3.configIO(EnableCounter0 = True, FIOAnalog = 15)
    ec0 = CounterConfig['EnableCounter0']
    if (ec0 == False):
        print('Counter0 not enabled anymore, exiting capture loop')
        return 0#return from function

	fd.write("Count\tTriggerState\tTime\tDeltaMS\n")
	rowstring=str(ncnt)+"\t0\t0\t0\n"
	fd.write(rowstring)
	print(rowstring)

	# for each timepoint ~1 ms??
	#if changed, log the timestamp
	#read the TTL status
	while 1:
		time.sleep(sleeptime)
		#readU3()
        if param.isU3==True:

            if (alivestatecnt >= alivestatecycles):
                #check on device status
                # if alive, do nothing but reset check Counter
                # if non-communicative, exit loop and provide error message
                CounterConfig = param.deviceU3.configIO()
                ec0 = CounterConfig['EnableCounter0']
                if (ec0 == False):
                    print('Counter0 not enabled anymore, exiting capture loop')
                    return 0 #will break loop and return from this function

                alivestatecnt = 0
            else:
                alivestatecnt = alivestatecnt + 1

            #check the counter status, this is the main read to the device.
            #The counter increments for each drop from high to low on a given line.
            #for the MRI setup, this is a TTL2_HIGH followed by a TTL2_LOW command in the pulse program
            #bitState=d.getFeedback(u3.BitStateRead(IONumber = 5))
			bitState=param.deviceU3.getFeedback(u3.Counter0(Reset = True))

        else:
			bitState=1
			time.sleep(sleeptime*100)

		#the state of the BitStateRead will use high/low.  The PV pulse sequences are programmed to low on trigger since the U3 counter advances on the low state.
		#  The labjack forums for this particular purpose state that if the pulse duration is 10ms or so, reading directly the state will be appropriate.  I believe this can be achieved in the Paravision sequences for certain applications, but not all.  The alternative it to use the digital counter, which can be read faster.  This is currently implemented here.
		if (bitState[0]>0):

			ntime=time.time()
			#this will cause an somewhat unpredictable delay from the actual change in the Counter0 states
            #however, it is better to use here than for each check to avoid overhead in each sampling.
            # our on scanner testing indicates we can get >1 ms repeatibility in times, which is precise enough for most of our applications.
			nowtime=(ntime - starttime)*1000.0
			elapsed=(ntime - ptime)*1000.0
			deltams=str("%.02f" % elapsed )
			elapsedms=str("%.02f" % nowtime )
			rowstring=str(ncnt)+"\t"+str(bitState[0])+"\t"+elapsedms+"\t"+deltams+"\n"

			fd.write(rowstring)
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

	# test for pvcmd functionality, returns with command not found if unsuccessful
	cmd="pvcmd -a ParxServer -r ListPs "
	process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	dummyOut, error = process.communicate()

	if "command not found"  in dummyOut:
		print "Start this logger from the PV terminal window, not just from any terminal.\npvcmd try unsuccessful."
		exit()

	if openandConfigureU3(u3Debugstate)==False:
		print "U3 not loaded or configured.\n  Doing logging with sleep timer."



	newscan=0
	triggBool=0

	prevDset=""
	print "Monitoring PV instance for scanning..."
	while  1:
		#this gets the scan that is currently running since it was started from the 'pipemaster' parent
		cmd="pvcmd -a ParxServer -r ListPs | grep -B 3 'pipeMaster' | grep -m 1 PSID | awk '{printf(\"%s\", $2)}'"
		process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		psid, error = process.communicate()

		if len(psid)>0:
			#print "Scan Active, PSID: "+psid
			cmd="pvcmd -a ParxServer -r DsetGetPath -psid "+psid+" -path EXPNO"
			#print cmd
			process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			datapath, error = process.communicate()
			pathlist=string.rsplit(datapath,'/',1)
			expno=pathlist[1]

			#print expno

			cmd="pvcmd -a ParxServer -r ParamGetValue -psid "+psid+" -param SUBJECT_study_instance_uid"
			process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			studyRegID, error = process.communicate()

			cmd="pvcmd -a JPingo -r DSetServer.GetScanStatus -registration "+studyRegID+" -expno "+expno
			process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			scanstatus, error = process.communicate()

			methodPath=datapath+"/method"

			if datapath != prevDset :
				newscan = 1
				pv=loadBruker(methodPath)

				#cmd="pvcmd -a ParxServer -r ParamGetValue -psid "+psid+" -param PVM_TriggerOutOnOff"
				#process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				#triggScanOutOn, error = process.communicate()
				#print triggScanOutOn
				#if "PVM_TriggerOutOnOff" in pv:
				#	trigOnOff = pv.get("PVM_TriggerOutOnOff","none")
				#else:
				#	trigOnOff=""
				#if trigOnOff[:2] == "On":
				#	triggBool = 1
				#	print "Triggering enabled for this scan: "+scanstatus
				#else:
				#	triggBool=0
					#print "Triggering not enabled for this scan"




			#print scanstatus


			if newscan==1 and (scanstatus=="SCANNING" or scanstatus == "RECO"):


				dstr=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
				logPath = datapath+"/TriggerOutLog"+dstr+".txt"

				print dstr

				fd = open(logPath,"w",buffering=0)

				print "Starting Process:\nLogging to "+logPath

				if param.isU3==True:
					print "Logging for ECG triggers from configured Console to LabJack U3."
				else:
					print "No U3.  Simulated logging with sleep timer."
				#start the logger in a separate process
				p = Process(target=CaptureAndWriteLog, args=(fd, Logsleeptime))
    				p.start()

                    #need to figure out how to get device status (return code 0) from this function if the device is non-communicative during logging.

    				#p.join() # this blocks until the process terminates

				prevDset=datapath
				newscan=0
			else:
				time.sleep(Monsleeptime)

		else:
			#print "No Scan Running: "
			if 'p' in locals():
				if p.is_alive()==1:
					print "Scan stopped, terminated logging "
					p.terminate()
					del p
					del pv
			if 'fd' in locals():
				if fd.closed==0:
					print "Closing files"
					fd.close()
					del fd

			prevDset=""
			time.sleep(Monsleeptime)
