# Flip Clock

The source code is available at: https://github.com/paexter/sbb-flip-clock

## Setup

Connect your clock with your Wifi to synchronize the time automatically with a time server.

1) Connect HDMI cable.
1) Connect USB keyboard and mouse. Use a USB hub or unplug the microphone temporarily.
1) Plug in the clock. It will boot up automatically once it is plugged in.
1) The clock should log in automatically. The user is `sbb`, password is `*`, and the hostname is `raspberrypi-clock`.
1) Open the Wifi panel and connect to your Wifi network. Note that only 2.4 GHz Wifi networks are supported.

## Turn on the Clock

1) Plug in the clock to turn it on. After about one minute the clock should start updating.
   * Note that booting up the clock fully takes about two minutes.
   * Note that setting the switch to *ON* does not turn on the clock.
   * If the switch is set to *ON* the clock will show the current time.
   * If the switch is set to *WAKE* the clock will show `12.34` and will listen to the wake word `hey clock`.
   * If the switch is set to *OFF* the clock will show `0.50`.

## Shutdown the Clock

1) Set the switch to the `OFF` position. The clock will show `0.50` and then count down to `0.00`. When it reaches `0.00` it will start the shutdown process. Wait 30 seconds for the clock to shut down. During that time the green LED on the Raspberry Pi will blink. Once the green LED is off, it is safe to unplug the clock.
