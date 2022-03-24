# screen-temp

This is an alternative to f.lux in windows.

I really wanted to have a schedule to set different temperatures at different times. Like I want it to be at 4500k after sunset then 1000k 2 hours before bedtime. The problem is that there are no existing programs that would both schedule and set the temperature as absurdly low as I want (at least in linux). So this is a good enough solution to filter the blue light in the best way possible.

# How it works
It has a set of hours and temperatures to work on and set the temperatures accordingly.
## For example
Let's say you need the screen temperature to end up at 2500 at 8PM. Let's also say
you need to have the temperature gradually change from the current temperature
to 2500 in the span of an hour. To do that you need to have a section in the config
file with the following information
* the starting temperature
* the ending temperature
* the starting time in HH:MM notation
* and finally the end time of the transition

the exact notation would be

```
[night]
start_temp = 6500
end_temp = 2500
start_time = 18:00
end_time = 20:00
```

**Note that the start_temp of a section NEEDS to be the same as the end of the previous temperature. Otherwise it's going to immediately go to the starting temperature of the current period.**
 I hope to fix this as soon as possible

What the program would do is change the temperature linearly across the given period
until the it is over. The program also would keep running in the background when
not in a transitional period, where it keeps setting the temperature to the end of the
closest period in the config file (If it's 9PM and the night period ended at 8PM
the temperature would be set to the end_temp of the night section every second until
the next transitional period).

        

# What it needs
There are a couple of python modules you need such as
* ConifgParser
* PyStray

There is also the redshift program that you can get from your distro's package manager.
`pacman -S redshift` or `apt-get install redshift`, etc

One more thing you need to do is to supply a configuration file to set the temperatures and the times
After creating the configuration file you need to change the line where it says `YOUR CONFIG LOCATION`
on line 14 on screen_temp.py

#In the future
* Validation of the configuration file
* There is no need to have the starting temperature of a pair if the ending temperature of the previous is going to be the same anyway. 
So fixing that should be a top priority
* Maybe if I get to it eventually but a GUI to change the configuration would be nice
#


Big thanks to IYIKON for the free icon

sunset icons PNG Designed By IYIKON from <a href="https://pngtree.com"> Pngtree.com</a>