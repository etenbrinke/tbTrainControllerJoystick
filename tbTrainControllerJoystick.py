#!/usr/bin/env python
# coding: Latin-1

# Load library functions we want
import time
import os
import sys
import pygame
import ThunderBorg
import logging
import random

logger = logging.getLogger('trainController')
hdlr = logging.FileHandler('/var/log/trainController.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

# Re-direct our output to standard error, we need to ignore standard out to hide some nasty print statements from pygame
sys.stdout = sys.stderr

# Setup the ThunderBorg
TB = ThunderBorg.ThunderBorg()
#TB.i2cAddress = 0x15                  # Uncomment and change the value if you have changed the board address
TB.Init()
if not TB.foundChip:
    boards = ThunderBorg.ScanForThunderBorg()
    if len(boards) == 0:
        logger.error ('No ThunderBorg found, check you are attached :)')
    else:
        logger.error ('No ThunderBorg at address %02X, but we did find boards:' % (TB.i2cAddress))
        for board in boards:
            logger.error ('    %02X (%d)' % (board, board))
        logger.error ('If you need to change the I²C address change the setup line so it is correct, e.g.')
        logger.error ('TB.i2cAddress = 0x%02X' % (boards[0]))
    sys.exit()
# Ensure the communications failsafe has been enabled!
failsafe = False
for i in range(5):
    TB.SetCommsFailsafe(True)
    failsafe = TB.GetCommsFailsafe()
    if failsafe:
        break
if not failsafe:
    logger.error ('Board %02X failed to report in failsafe mode!' % (TB.i2cAddress))
    sys.exit()

# Settings for the joystick
# index numbers for each control: https://www.piborg.org/blog/rpi-ps3-help
axisUpDown = 1                          # Joystick axis to read for up / down position
axisUpDownInverted = True               # Set this to True if up and down appear to be swapped
buttonEmergencyBreak = 14               # Joystick button number (Cross) for the Emergency Break
buttonSlowAutoStop = 15                 # Joystick button number (Square) for slow auto stop
buttonAxisMotionMode = 11               # Joystick button number for selecting Axis Motion mode (R1)
buttonSlowAutoStartForward = 12         # Joystick button number (Triangle) for slow auto forward to half speed of max speed
buttonSlowAutoStartReverse = 13         # Joystick button number (Circle) for slow auto reverse to half speed of max speed
buttonRandomModeOn = 10                 # Joystick button number for selecting random mode ON (L1)
buttonRandomModeOff = 8                 # Joystick button number for selecting random mode OFF (L2)

# Program settings
interval = 0.00                         # Time between updates in seconds, smaller responds faster but uses more processor time

# Settings for speed control
accelerationFactor = 0.001              # Acceleration factor for speedup and slow down
slowDeAccelerationFactor = 0.00003      # Deacceleration factor for auto stop
slowAccelerationFactor = 0.00003        # Acceleration factor for auto start
slowAutoStartMaxSpeed = 0.60            # Max speed for slow auto forward and reverse
slowAutoStartMediumSpeed = 0.45         # Medium speed for slow auto forward and reverse (only used in random mode)
zeroOffsetSpeed = 0.01                  # A value smaller (bigger in case speed is negative) is considered as zero speed
randomDriveRange = 5000                 # Choice value between 0 and randomDriveRange for random drive mode

# Power settings
voltageIn = 12.0                        # Total battery voltage to the ThunderBorg
voltageOut = 12.0                       # Maximum motor voltage

# Setup the power limits
if voltageOut > voltageIn:
    maxPower = 1.0
else:
    maxPower = voltageOut / float(voltageIn)

# Show battery monitoring settings
battMin, battMax = TB.GetBatteryMonitoringLimits()
battCurrent = TB.GetBatteryReading()
logger.info ('Battery monitoring settings:')
logger.info ('    Minimum  (red)     %02.2f V' % (battMin))
logger.info ('    Half-way (yellow)  %02.2f V' % ((battMin + battMax) / 2))
logger.info ('    Maximum  (green)   %02.2f V' % (battMax))
logger.info ('')
logger.info ('    Current voltage    %02.2f V' % (battCurrent))
logger.info ('')

# Setup pygame and wait for the joystick to become available
TB.MotorsOff()
TB.SetLedShowBattery(False)
TB.SetLeds(0,0,1)
os.environ["SDL_VIDEODRIVER"] = "dummy" # Removes the need to have a GUI window
pygame.init()
pygame.display.set_mode((1,1))
logger.info ('Waiting for joystick...')
while True:
    try:
        try:
            pygame.joystick.init()
            # Attempt to setup the joystick
            if pygame.joystick.get_count() < 1:
                # No joystick attached, set LEDs blue
                TB.SetLeds(0,0,1)
                pygame.joystick.quit()
                time.sleep(0.1)
            else:
                # We have a joystick, attempt to initialise it!
                joystick = pygame.joystick.Joystick(0)
                break
        except pygame.error:
            # Failed to connect to the joystick, set LEDs blue
            TB.SetLeds(0,0,1)
            pygame.joystick.quit()
            time.sleep(0.1)
    except KeyboardInterrupt:
        # CTRL+C exit, give up
        logger.info ('User aborted')
        TB.SetCommsFailsafe(False)
        TB.SetLeds(0,0,0)
        sys.exit()
logger.info ('Joystick found')
joystick.init()
TB.SetLedShowBattery(True)
ledBatteryMode = True
try:
    running = True
    hadEvent = False
    hadBreak = False
    upDown = 0
    driveSpeed = 0
    randomMode = False
    goalSpeed = 0

    # Loop indefinitely
    while running:
        # Get the latest events from the system
        hadEvent = False
        # Control train randomly (only drive forward)
        if randomMode and random.randint(0,randomDriveRange) == 0:
            # Choose a goal speed
            # Actually these goal speeds very much depends on the type of locomotive as they respond all differently
            goalSpeed = random.choice([0, 0, 0.40, 0.45, 0.50, 0.55])
            if driveSpeed < goalSpeed:
                logger.info ('Slowly increase forward speed by random mode, driveSpeed slowly up from %02.2f to %02.2f' % (driveSpeed, goalSpeed))
                while driveSpeed < goalSpeed:
                    driveSpeed += slowAccelerationFactor
                    if driveSpeed > goalSpeed:
                        driveSpeed = goalSpeed
                    TB.SetMotor1(driveSpeed * maxPower)
            elif driveSpeed > goalSpeed:
                logger.info ('Slowly descrease forward speed by random mode, driveSpeed slowly down from %02.2f to %02.2f' % (driveSpeed, goalSpeed))
                while driveSpeed > goalSpeed:
                    driveSpeed -= slowDeAccelerationFactor
                    if driveSpeed < goalSpeed or driveSpeed < zeroOffsetSpeed:
                        driveSpeed = goalSpeed
                    TB.SetMotor1(driveSpeed * maxPower)
        # Control train by joystick
        events = pygame.event.get()
        # Handle each event individually
        for event in events:
            if event.type == pygame.QUIT:
                # User exit
                running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                # A button on the joystick just got pushed down
                if joystick.get_button(buttonEmergencyBreak):
                    logger.info ('Emergency Break button pressed, driveSpeed %02.2f set to 0.00' % driveSpeed)
                    driveSpeed = 0
                    TB.SetMotor1(driveSpeed)
                    break
                if joystick.get_button(buttonRandomModeOn):
                    logger.info ('Random mode ON')
                    randomMode = True
                    break
                if joystick.get_button(buttonRandomModeOff):
                    logger.info ('Random mode OFF')
                    randomMode = False
                    break
                if joystick.get_button(buttonSlowAutoStop):
                    logger.info ('Slow Auto Stop button pressed, driveSpeed slowly down from %02.2f to 0.00' % driveSpeed)
                    if driveSpeed < 0:
                        while driveSpeed < 0:
                            driveSpeed += slowDeAccelerationFactor
                            if driveSpeed > -zeroOffsetSpeed:
                                driveSpeed = 0
                            TB.SetMotor1(driveSpeed * maxPower)
                    elif driveSpeed > 0:
                        while driveSpeed > 0:
                            driveSpeed -= slowDeAccelerationFactor
                            if driveSpeed < zeroOffsetSpeed:
                                driveSpeed = 0
                            TB.SetMotor1(driveSpeed * maxPower)
                    break
                if joystick.get_button(buttonSlowAutoStartForward) and driveSpeed < zeroOffsetSpeed:
                    # go drive forward only if we currently drive backward or are standing still 
                    logger.info ('Slow Auto Forward button pressed, driveSpeed slowly up from %02.2f to %02.2f' % (driveSpeed, slowAutoStartMaxSpeed))
                    while driveSpeed < slowAutoStartMaxSpeed:
                        driveSpeed += slowAccelerationFactor
                        if driveSpeed > slowAutoStartMaxSpeed:
                            driveSpeed = slowAutoStartMaxSpeed
                        TB.SetMotor1(driveSpeed * maxPower)
                    break
                if joystick.get_button(buttonSlowAutoStartReverse) and driveSpeed > -zeroOffsetSpeed:
                    # go drive reverse only if we currently drive forward or are standing still 
                    logger.info ('Slow Auto Reverse button pressed, driveSpeed slowly up from %02.2f to %02.2f' % (driveSpeed, -slowAutoStartMaxSpeed))
                    while driveSpeed > -slowAutoStartMaxSpeed:
                        driveSpeed -= slowAccelerationFactor
                        if driveSpeed < -slowAutoStartMaxSpeed:
                            driveSpeed = -slowAutoStartMaxSpeed
                        TB.SetMotor1(driveSpeed * maxPower)
                    break
                hadEvent = True
            elif event.type == pygame.JOYAXISMOTION:
                # A joystick has been moved
                hadEvent = True
            if hadEvent:
                # A button on the joystick just got pushed down
                # Read axis positions (-1 to +1)
                if axisUpDownInverted:
                    upDown = -joystick.get_axis(axisUpDown)
                else:
                    upDown = joystick.get_axis(axisUpDown)
                # Apply drive speed
                driveSpeed = driveSpeed + (upDown * accelerationFactor)
                if driveSpeed > 1:
                    driveSpeed = 1
                elif driveSpeed < -1:
                    driveSpeed = -1
                # Set motor 1 to the new speeds
                if joystick.get_button(buttonAxisMotionMode):
                    TB.SetMotor1(upDown * maxPower)
                else:
                    TB.SetMotor1(driveSpeed * maxPower)
        # Change LEDs to purple to show motor faults
        if TB.GetDriveFault1() or TB.GetDriveFault2():
            if ledBatteryMode:
                TB.SetLedShowBattery(False)
                TB.SetLeds(1,0,1)
                ledBatteryMode = False
        else:
            if not ledBatteryMode:
                TB.SetLedShowBattery(True)
                ledBatteryMode = True
        time.sleep(interval)
    # Disable all drives
    TB.MotorsOff()
except KeyboardInterrupt:
    # CTRL+C exit, disable all drives
    TB.MotorsOff()
    TB.SetCommsFailsafe(False)
    TB.SetLedShowBattery(False)
    TB.SetLeds(0,0,0)
