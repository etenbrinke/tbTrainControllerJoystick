# ThunderBorg Train Controller for PlayStation 3 Controller

Control Analog H0 train with the powerful dual motor control board ThunderBoard, Playstation 3 controller and the Raspberry Pi.

The code is based on tbJoystick.py, part of the examples https://www.piborg.org/blog/build/thunderborg-build/thunderborg-examples

## ThunderBorg dual channel motor control board

Although the board is developed to make awesome robots it is also very suitable for driving old analog H0 model trains.
It can drive two motors from 7V to 35V and can deliver 5A per motor. In this project we supplied the board with 20 Volt and only use a single motor connection for driving our train.
The board will deliver a PWM signal fully controlled by the Pi, so in our case a -20V till 20V track voltage to control our train in both directions.
If you want to go big you can plug in more boards on the same Pi up to 200 channels, this equals to 200 fully controlled train tracks. I'm already happy with one!

Checkout: https://www.piborg.org/motor-control-1135/thunderborg

## Controller settings

The following Axis and buttons has been defined:

```
# Settings for the joystick
axisUpDown = 1                          # Joystick axis to read for up / down position
axisUpDownInverted = False              # Set this to True if up and down appear to be swapped
buttonEmergencyBreak = 14               # Joystick button number (Cross) for the Emergency Break
buttonSlowAutoStop = 15                 # Joystick button number (Square) for slow auto stop
buttonAxisMotionMode = 11               # Joystick button number for selecting Axis Motion mode (R1)
buttonSlowAutoStartForward = 12         # Joystick button number (Triangle) for slow auto forward to half speed of max speed
buttonSlowAutoStartReverse = 13         # Joystick button number (Circle) for slow auto reverse to half speed of max speed
```

With the left Axis the train speed can be increased or descreased in both forward and reverse direction. Holding it Up slowly increases the speed in forward direction. Holding it down increases speed in reverse direction.
When train is speeding forward, holding Down will slow the train down and finally increases speed in reverse direction. Same for the other direction.
Pressing the R1 button while using the left Axis will change the Axis Motion Mode: holding Up and Down will directly translated into the train speed without any steps. Be carefull, passengers might not like this ;-)

Other buttons:
* Cross: Emergency Break, train will stop directly
* Square: Train will stop slowly from the direction it was driving
* Triangle: Slowly increase forward speed up to 75 % (can be changed via ```slowAutoStartMaxSpeed```) of max speed
* Circle: Slowly increase reverse speed up to 75 % (can be changed via ```slowAutoStartMaxSpeed```) of max speed

The following speed control settings can be adjusted:

```
# Settings for speed control
accelerationFactor = 0.001              # Acceleration factor for speedup and slow down
slowDeAccelerationFactor = 0.00005      # Deacceleration factor for auto stop
slowAccelerationFactor = 0.00005        # Acceleration factor for auto start
slowAutoStartMaxSpeed = 0.75            # Max speed for slow auto forward and reverse
zeroOffsetSpeed = 0.01                  # A value smaller (bigger in case speed is negative) is considered as zero speed
```

## Auto start controller on Pi

To autostart the controller program after a reboot or startup of the Pi the following has been added to the crontab:

```
@reboot sleep 30 ; sudo python /home/eptb/thunderborg/tbTrainControllerJoystick.py
```

The sleep is to give the owner 30 seconds to activate the PS3 controller attached via USB or bluethooth before the program starts and tries to find the joystick
