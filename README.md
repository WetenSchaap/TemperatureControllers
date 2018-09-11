Temp-controllers

Python code for controlling waterbaths and other temperature controllers at WZI-IOP @ UvA.
This code makes use of the PySerial package to controll the serialports the devices are connected to.

Julabo_control.py shows an example of how we could use this code, in this case with the Julabo waterbath.
classywatherbaths.py is now the most recent class. Simonexp.py is still functional for the Julabo and the electrical controller, but has fewer options and does not allow multiple units to be controlled from the same PC.

Currently supported devices:
* Julabo
* Haake F6
* Haake Phoenix
* Electrical controller

However, it should be easy to implement more devices, see classywaterbaths.py for details.
