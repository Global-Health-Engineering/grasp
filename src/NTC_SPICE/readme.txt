
Installation of NTC Thermistor Model Library	    Date: January 17, 2024
===============================================================

The model library of NTC Thermistors for the 
circuit design program PSpice
includes the following two files:

NTC_Library.LIB		ASCII data file:
	        This file respresents the current library and 
	        contains the data required for calculation. 

NTC_Library.OLB		Symbol data file:
	        This file contains the terminal/graphics information
	        required by the graphic user interface "Schematics"
              


If you want to keep your old files, please make a copy. The new library will
overwrite the existing files.
How to install the files:

1.	Copy the two files to the directory of the library files:
	...\CAPTURE\LIBRARY\PSPICE 
	
2.	In ORCAD-environment: Go to menu "Pspice" 
	-> submenu "Edit Simulation Settings"
	The window "Simulation Setting" appears. Choose "Libraries".
        Click field "Browse" to select path where the library is located.
        Click "Add as Global" for permanent integration of the library
        or "Add to Design" for temporary use.


