# Temp-controllers

Python code for controlling waterbaths and other temperature controllers programatically at WZI-IOP @ UvA.

This code makes use of the PySerial package to control the serial ports the devices are connected to.

This code is desiigned to run in an interactive python enviroment, ideally just in an IDE, like Spyder. That way you can interactively play around, but also run scripts while not screwing up anything. The `Julabo_control.py` script shows an example of how we could use this code, in this case with the Julabo waterbath. The `classywatherbaths.py` script is where the actual magic happens, and needs to be imported (or run interactively) before you do anything else. 

The `tempcontroller_info.log` file is a text file that is generated automatically when you use the `classywatherbaths.py` script. It contains a log of all commands etc. which you send to the device with a timestamp, so you can look back and see what you did.

Internally, `classywatherbaths.py` makes use of a separate class for every type of waterbath. It should be easy to implement more devices, see `classywaterbaths.py` for details on how to do that. This is definitly not the most elegant way to do it, but it does work and gave me time to practice my Pythobn skills.

The `Simonexp.py` 'legacy' code is still functional for the Julabo and the electrical controller, but has fewer options and does not allow multiple units to be controlled from the same PC.

Currently supported devices:
* Julabo
* Haake F6
* Haake Phoenix
* Electrical controller