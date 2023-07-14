How to use this program
This program takes tab-separated txt or rtf files as inputs. These files are 
exported from AD Instruments equipment. The user then selects the sampling rate 
(typically 1000hz) and then elects whether the data has been blocked out using a pulse 
or if the user would like to select their own timestamps to chunk the data from. The program then 
presents the user with a settings dialogue box. If the user has selected to block the data using a pulse, 
they will be asked to select which column contains the pulse and which contains the ECG data. If the user 
chooses their own timestamps, they will have the option to select the start and finishing times. If they 
would like to analyse the whole dataset, they can select that too.
In both cases, the user can select whether to apply a frequency filter to the data to denoise it. This filter
removes frequencies less than 0.5hz and greater than 15hz. 
The program then uses an algorithm to detect R Peaks before displaying the data in the chart.
Once the settings have been chosen, the program will display the timeseries data. If the data is divided by pulses,
the user can scroll through the sections. 
Buttons to interact with the GUI:
    Left click: Manually add an R Peak to the timeseries 
    Right click: Manually remove an R Peak from the timeseries 
    Q: Position the largest interval between two  detected R Peaks in the centre of the graph 
    W: Position the smallest interval between two detected R Peaks in the centre of the graph 
    Numbers 1 - 5: Choose the x-axis scaling of the graph (1 = 30 seconds, 2 = 15 seconds,
     3 = 10 seconds, 4 = 5 seconds, 5 = 3 seconds)
The button in the top-right of the window allows the user to overlay either the unfiltered or the filtered 
timeseries depending on their initial selection. This allows for verification of R Peaks. 
The button below the Select-File button switches between the R-Peaks interval plot and a histogram 
of the R-R intervals. 
The button in the bottom left allows the user to r-detect R Peaks, this removes R PEaks which are too close to each other 
(indicating a false-positive), saving the user time manually deleting them 
Finally, the user can export either the R-R intervals (time differences between R Peaks) or the location 
and voltage of the R Peaks. This opens a dialogue box to select the location and then automatically generates 
a file name based on the originally-imported file. 
