# PVTriggerCapture

A python script in combination with the LabJack U3 device to record timestamps in MRI sequences on the Paravision platform.

Briefly,
Connect the labjack to the USB of the console and the TTL2 port (BNC)
Within the sequences, functions that use TTL2_HIGH followed by TTL2_LOW will output the appropraite pulses for recording.

Start the captureTriggers.py in a terminal window on the console.

The program will continuously monitor the status of paravision for the current setting (scanning, idle, etc).
Once a sequence starts running, the program will start to monitor the labjack/usb input and record the time between successive TTL2 pulses as well as the cumulative time since it first started.
Importantly, it will record the data to a text file stored in the same location as the imaging data. 
If the scan stops, either by completetion or error, the recording will stop and wait for the next scan.
Basically, the user does not have to do anything other than start it initially (although monitoring to see it is working is useful), which can be seen in the terminal window.

In our implementation, we used it to record the post-label delays (PLD) in arterial spin labelling with cardiac gating. Therefore, the PLDs were variable and this tool enabled us to record the actual delays for all datapoints and use that information appropriately.

