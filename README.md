# Temp-controllers

Python code for controlling waterbaths and other temperature controllers at WZI-IOP @ UvA.
This code makes use of the PySerial package to controll the serial ports the devices are connected to.

The *Julabo_control.py* script shows an example of how we could use this code, in this case with the Julabo waterbath.
The *classywatherbaths.py* script is the most recent code to manage the temperature controlers. It makes use of a seperate class for every type of waterbath.

The *Simonexp.py* 'legacy' code is still functional for the Julabo and the electrical controller however, but has fewer options and does not allow multiple units to be controlled from the same PC.

Currently supported devices:
* Julabo
* Haake F6
* Haake Phoenix
* Electrical controller

However, it should be easy to implement more devices, see *classywaterbaths.py* for details on hoe to do that.
