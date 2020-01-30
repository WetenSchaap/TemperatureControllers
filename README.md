# Temp-controllers

Python code for controlling waterbaths and other temperature controllers at WZI-IOP @ UvA.
This code makes use of the PySerial package to control the serial ports the devices are connected to.

The *Julabo_control.py* script shows an example of how we could use this code, in this case with the Julabo waterbath.
The *classywatherbaths.py* script is (should be) the most recent code to manage the temperature controllers. It makes use of a separate class for every type of waterbath.
The *tempcontroller_info.log* file is a text file that is generated automatically when you use the *classywatherbaths.py* script. It contains a log of all commands etc. which you send to the device with a timestamp, so you can look back and see what you did.

The *Simonexp.py* 'legacy' code is still functional for the Julabo and the electrical controller, but has fewer options and does not allow multiple units to be controlled from the same PC.

Currently supported devices:
* Julabo
* Haake F6
* Haake Phoenix
* Electrical controller

However, it should be easy to implement more devices, see *classywaterbaths.py* for details on how to do that.
