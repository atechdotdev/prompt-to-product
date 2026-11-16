"""build_shelf_index - write shelf_index.json, the off-the-shelf parts
Prompt2Product offers, from the FreeCAD Parts Library at shelf.REVISION.

    GITHUB_TOKEN=<token, optional> freecadcmd projects/build_shelf_index.py
    SHELF_ONLY=a,b freecadcmd ...          # (re)build only these parts, keep the rest
    SHELF_MODE=authors  freecadcmd ...     # refresh only the authors
    SHELF_MODE=pictures [SHELF_ONLY=a,b] freecadcmd ...  # draw the pictures

CURATED below is the list and everything we SAY about each part: what it
is, its wiring where a datasheet settles it (nothing is said otherwise),
and notes for the agent. Everything else is MEASURED or READ here:
  * path, git blob id and byte size from the repository tree at REVISION;
  * size_mm from the part's own mesh (the STEP downloaded, its blob id
    checked, meshed as user_parts meshes every STEP);
  * authors from the file's git history (the library's licence: "See
    commit details to find the authors of each Part"), oldest first;
  * thumb: the library's own picture of the part's .FCStd, when it has one
    (build_index.py names it md5(quoted path)).png).
The GitHub API allows 60 unauthenticated requests an hour; one per part is
made for its history, so set GITHUB_TOKEN for a full build.
"""
import hashlib
import json
import os
import sys
import tempfile
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import shelf  # noqa: E402

E, P, M, W, X = "electronics", "power", "motor", "wheel", "mechanical"


def el(interface=None, voltage_v=None, wiring=None, connectors=None):
    d = {"interface": interface, "voltage_v": voltage_v, "wiring": wiring,
         "connectors": connectors}
    return {k: v for k, v in d.items() if v is not None}


#: key: (group, path, display name, category, electrical, description, agent notes)
CURATED = {
    # ---------------------------------------------------------------- boards
    "arduino_nano": ("boards", "Computing/SingleBoardComputers/Arduino/Nano-Rev3_0.step",
                     "Arduino Nano (Rev3)", E,
                     el("usb", 5, "ATmega328P; 5 V logic", "USB Mini-B; 2 rows of 2.54 mm pins"),
                     "Small microcontroller board (ATmega328P) with a USB Mini-B socket.",
                     "Leave the USB Mini-B socket reachable through a wall opening, and "
                     "room above the pin rows for wires or a socket."),
    "arduino_uno_compatible": ("boards", "Computing/SingleBoardComputers/Arduino/freaduino-uno.step",
                               "Freaduino Uno (Arduino Uno compatible)", E,
                               el("usb", 5, "ATmega328P; 5 V logic"),
                               "Arduino Uno-compatible board (Freaduino), the Uno's size and "
                               "mounting holes.",
                               "Open the USB and DC-jack end of the board to the outside. Mount "
                               "it on standoffs through its holes; leave room above the headers "
                               "for shields or wires."),
    "arduino_mega": ("boards", "Computing/SingleBoardComputers/Arduino/arduino-mega.step",
                     "Arduino Mega 2560", E, el("usb", 5, "ATmega2560; 5 V logic"),
                     "Large Arduino board (ATmega2560) with many pins.",
                     "Open the USB and DC-jack end to the outside; mount it on standoffs "
                     "through its holes; leave room above the headers for wires."),
    "esp32_devkit": ("boards", "Computing/SingleBoardComputers/ESP32/ESP32_DOIT_DevKit_v1/ESP32_DOIT_DevKit_V1.step",
                     "ESP32 DevKit V1 (DOIT)", E,
                     el("usb", None, "ESP32 with Wi-Fi and Bluetooth; 3.3 V logic", "Micro-USB"),
                     "ESP32 Wi-Fi/Bluetooth development board with a Micro-USB socket.",
                     "Keep the antenna end of the module clear of metal and of thick walls "
                     "near it (no metal in front of it); leave the Micro-USB socket reachable."),
    "raspberry_pi_4b": ("boards", "Computing/SingleBoardComputers/Raspberry/Raspberry Pi 4B/Raspberry Pi 4B.step",
                        "Raspberry Pi 4 Model B", E,
                        el("usb", 5, "powered by 5 V over USB-C",
                           "USB-C power, 2 micro-HDMI, 4 USB-A, Ethernet, 3.5 mm jack"),
                        "Single-board computer with USB-C power, two micro-HDMI, four USB-A "
                        "and Ethernet.",
                        "Open the connector edges you need (USB/Ethernet end, USB-C and HDMI "
                        "side) to the outside; it runs warm: vent the case or leave room for a "
                        "heatsink or fan over the processor. Mount on M2.5 standoffs through "
                        "its four holes."),
    "raspberry_pi_pico": ("boards", "Computing/SingleBoardComputers/Raspberry/Raspberry Pi Pico/Pico-R3.step",
                          "Raspberry Pi Pico", E,
                          el("usb", None, "RP2040; 3.3 V logic", "Micro-USB"),
                          "Small RP2040 microcontroller board with a Micro-USB socket.",
                          "Leave the Micro-USB socket reachable and room for pins or wires "
                          "along both long edges."),
    # --------------------------------------------------------------- sensors
    "hc_sr04": ("sensors", "Sensors/Ultrasonic Sensors/HC-SR04.step",
                "HC-SR04 ultrasonic distance sensor", E,
                el("gpio", 5, "trigger and echo pins"),
                "Ultrasonic distance sensor with two round transducers.",
                "Both transducers must look out through the wall: one round hole each, a "
                "little wider than the transducer, with nothing in front of them. Point them "
                "at what is measured."),
    "sharp_gp2y0a41": ("sensors", "Electronics Parts/Optical/SHARP/0A41SK/SHARP-0A41SK.step",
                       "Sharp GP2Y0A41SK0F IR distance sensor (4-30 cm)", E,
                       el("analog", 5, "analog voltage out"),
                       "Infrared distance sensor, 4 to 30 cm, analog output.",
                       "The two lenses (emitter and receiver) must see out: an opening over "
                       "both, or an IR-clear window; never cover them with ordinary plastic."),
    "sharp_gp2y0a02": ("sensors", "Electronics Parts/Optical/SHARP/2Y0A02/SHARP-2Y0A02.step",
                       "Sharp GP2Y0A02YK0F IR distance sensor (20-150 cm)", E,
                       el("analog", 5, "analog voltage out"),
                       "Infrared distance sensor, 20 to 150 cm, analog output.",
                       "The two lenses (emitter and receiver) must see out: an opening over "
                       "both, or an IR-clear window."),
    "maxsonar_mb1010": ("sensors", "Sensors/Ultrasonic Sensors/MaxSonar/MB1010/MaxSonar-MB1010.step",
                        "MaxBotix LV-MaxSonar-EZ1 (MB1010)", E,
                        el("analog", None, "2.5-5.5 V; analog, serial or pulse-width output"),
                        "Ultrasonic range finder with one transducer.",
                        "The transducer must look out through a round hole with nothing in "
                        "front of it."),
    "raspi_camera_wide": ("sensors", "Sensors/Cameras/Wide-170-Angle-Raspi-Camera.step",
                          "Raspberry Pi camera, 170° wide angle", E,
                          el("other", None, None, "CSI ribbon cable"),
                          "Camera board with a 170° wide-angle lens for the Raspberry Pi.",
                          "Its view is very wide: the lens opening must be wide and short "
                          "(countersunk, wider outside) or the case shows in the picture. "
                          "Leave a path for the flat ribbon cable."),
    "photoresistor": ("sensors", "Electronics Parts/Photoresistor/Photoresistor.step",
                      "Photoresistor (LDR)", E, el("analog"),
                      "Light-dependent resistor.",
                      "It reads the light that reaches it: an opening or a clear window over "
                      "its face."),
    "inductive_proximity": ("sensors", "Electronics Parts/Inductors/Inductive_sensor/Inductive-Proximity-Sensor.step",
                            "Inductive proximity sensor (cylindrical)", E, el("gpio"),
                            "Threaded cylindrical sensor that detects metal at its face.",
                            "Mount it by its thread through a wall or bracket hole with its "
                            "two nuts; its face must be free, no metal round the face."),
    "gnss_antenna": ("sensors", "Electronics Parts/Antennas/Antenna-GNSS-STA-901A.step",
                     "GNSS antenna (STA-901A)", E, el("other"),
                     "Satellite-navigation (GPS) antenna.",
                     "It needs a view of the sky: top of the product, under plastic only, "
                     "never under metal."),
    # ---------------------------------------------------------------- motors
    "sg90_servo": ("motors", "Electrical Parts/Servos/SG-90/Servo-sg90.step",
                   "SG90 micro servo", M, el("pwm", 5, "4.8-6 V; PWM signal", "3-wire lead"),
                   "Micro hobby servo, about 180° of travel.",
                   "Hold it by its mounting ears (two screws) in a pocket the body's size; its "
                   "output shaft and horn need room to swing; leave a path for the 3-wire lead."),
    "emax_es08a": ("motors", "Electrical Parts/Servos/Emax-ES08A/Emax-es08A.step",
                   "Emax ES08A micro servo", M, el("pwm", None, "PWM signal", "3-wire lead"),
                   "Micro hobby servo.",
                   "Hold it by its mounting ears in a pocket the body's size; the horn needs "
                   "room to swing."),
    "futaba_s3003": ("motors", "Electrical Parts/Servos/Futaba3003/Futaba3003.stp",
                     "Futaba S3003 standard servo", M, el("pwm", None, "4.8-6 V; PWM signal", "3-wire lead"),
                     "Standard-size hobby servo.",
                     "Hold it by its four mounting ears; the horn needs room to swing."),
    "springrc_sm_s4303r": ("motors", "Electrical Parts/Servos/SpringRC-SM-S4303R/SM-S4303R.step",
                           "SpringRC SM-S4303R continuous-rotation servo", M,
                           el("pwm", None, "PWM signal sets speed and direction", "3-wire lead"),
                           "Standard-size servo that turns continuously (a geared motor "
                           "driven by a servo signal).",
                           "Hold it by its four mounting ears; it can drive a wheel directly "
                           "on its horn."),
    "stepper_28byj48": ("motors", "Electrical Parts/Motors/Stepper/28BYJ-48/28BYJ-48.step",
                        "28BYJ-48 geared stepper motor", M,
                        el("other", 5, "unipolar; needs a driver (ULN2003 board)", "5-wire lead"),
                        "Small 5 V geared stepper motor.",
                        "Mount it by its two ears; the shaft is off-centre. Leave a path for "
                        "the 5-wire lead to its driver board."),
    "nema17_stepper_fc": ("motors", "Electrical Parts/Motors/Stepper/NEMA/NEMA_17_with_connector.step",
                          "NEMA 17 stepper motor (with connector)", M,
                          el("other", None, "bipolar; needs a stepper driver"),
                          "Standard 42 mm stepper motor with its cable connector.",
                          "Mount it by the four screws in its face; leave the connector "
                          "reachable and air round the body (it runs warm)."),
    "tt_gearmotor": ("motors", "Electrical Parts/Motors/DC motor/Yellow_gearmotor/straight/Yellow_gearmotor_straight.step",
                     "TT gear motor (yellow, straight)", M, el("power", None, "about 3-6 V DC"),
                     "The common yellow hobby gear motor, double output shaft.",
                     "Hold it by its two through-holes; a TT wheel fits its shaft. Leave a "
                     "path for its two wires."),
    "tt_gearmotor_l": ("motors", "Electrical Parts/Motors/DC motor/Yellow_gearmotor/L_shape/Yellow_gearmotor_L.step",
                       "TT gear motor (yellow, right angle)", M, el("power", None, "about 3-6 V DC"),
                       "The common yellow hobby gear motor, motor at right angles to the shaft.",
                       "Hold it by its through-holes; a TT wheel fits its shaft."),
    "pololu_micro_298": ("motors", "Electrical Parts/Motors/DC motor/Pololu-Micro/Pololu-298_1-6V.step",
                         "Pololu micro metal gearmotor, 298:1, 6 V", M, el("power", 6),
                         "Tiny metal gearmotor (N20 size), 298:1.",
                         "Clamp the gearbox in a bracket or a pocket with a strap; the motor "
                         "end needs its two terminals reachable."),
    "cqrobot_37d": ("motors", "Electrical Parts/Motors/cqrobot_37d/CQRobot_37D_90to1_64CPR.step",
                    "CQRobot 37D gearmotor, 90:1, with encoder", M,
                    el("power", None, "64 CPR encoder on the motor"),
                    "37 mm metal gearmotor with an encoder.",
                    "Mount it by the screws in its gearbox face; leave room behind the "
                    "encoder for its cable."),
    "faulhaber_2342": ("motors", "Electrical Parts/Motors/DC motor/FAULHABER 2342L-012CPR/FAULHABER_2342L-012CPR.step",
                       "Faulhaber 2342L012CR DC motor", M, el("power", 12),
                       "Precision 23 mm DC motor, 12 V.",
                       "Mount it by the screws in its face; keep its shaft aligned with what "
                       "it drives."),
    "dc_motor_encoder": ("motors", "Electrical Parts/Motors/DC motor/Mabuchi-Encoder/DCMotorEncoder.step",
                         "DC motor with encoder (Mabuchi)", M, el("power"),
                         "Small DC motor with an encoder disc on the back.",
                         "Mount it by its face; leave room behind it for the encoder."),
    "mini_vacuum_pump": ("motors", "Electrical Parts/Motors/Vacuum Pump/Mini vacuum pump.step",
                         "Mini vacuum / air pump", M, el("power"),
                         "Small diaphragm air pump.",
                         "Leave its two nozzles reachable for tubing; it vibrates: mount it on "
                         "soft pads, not hard against the case."),
    "fan_40mm": ("motors", "Electrical Parts/fans/fan-40x40mm.step", "Fan, 40 mm", M, el("power"),
                 "40 mm axial cooling fan.",
                 "Air must reach both faces: a grille in the wall over it (not a solid wall) "
                 "and an inlet elsewhere so air flows through. Mount by its corner holes."),
    "fan_50mm": ("motors", "Electrical Parts/fans/fan-50x50mm.step", "Fan, 50 mm", M, el("power"),
                 "50 mm axial cooling fan.",
                 "A grille over it and an inlet elsewhere; mount by its corner holes."),
    "blower_50mm": ("motors", "Electrical Parts/fans/blower-50x50mm.step", "Blower fan, 50 mm", M,
                    el("power"), "50 mm radial (blower) fan: air in at the face, out at the side.",
                    "Leave its face inlet open and duct its side outlet to a vent."),
    "tt_wheel_65mm": ("motors", "Electrical Parts/Motors/DC motor/Yellow_wheel_65mm/Yellow_wheel_65mm.step",
                      "Wheel for TT gear motor, 65 mm", W, None,
                      "65 mm rubber-tyred wheel that fits the TT gear motor.",
                      "Give it clearance all round inside any wheel arch; it sits on the TT "
                      "motor's shaft."),
    # ----------------------------------------------------------------- power
    "battery_aa": ("power", "Electrical Parts/Batteries/battery-AA.step", "AA battery", P,
                   el("power", 1.5), "AA cell.",
                   "Hold it in a holder or a clip; leave a door to change it."),
    "battery_aaa": ("power", "Electrical Parts/Batteries/battery-AAA.step", "AAA battery", P,
                    el("power", 1.5), "AAA cell.",
                    "Hold it in a holder or a clip; leave a door to change it."),
    "battery_holder_4aaa": ("power", "Electrical Parts/Batteries/battery-holder-4-AAA.step",
                            "Battery holder, 4 × AAA", P, el("power"),
                            "Holder for four AAA cells.",
                            "Put it behind a battery door the user can open; leave a path "
                            "for its two wires."),
    "battery_holder_8aaa": ("power", "Electrical Parts/Batteries/battery-holder-8-AAA.step",
                            "Battery holder, 8 × AAA", P, el("power"),
                            "Holder for eight AAA cells.",
                            "Put it behind a battery door the user can open."),
    "lipo_240mah": ("power", "Electrical Parts/Batteries/battery_lipo_3_7v_240mAh.step",
                    "LiPo battery, 3.7 V 240 mAh", P, el("power", 3.7),
                    "Small lithium-polymer pouch cell.",
                    "Give it a pocket with a little room to swell, nothing sharp against it, "
                    "away from hot parts; never clamp it."),
    "lm2596_buck": ("power", "Electrical Parts/DCDC/LM2596S_Buck_Module_43x21/LM2596S_Buck_Module_43x21.step",
                    "LM2596 buck converter module", P,
                    el("power", None, "adjustable step-down regulator (LM2596S)"),
                    "Adjustable step-down voltage regulator board.",
                    "Leave its trim potentiometer reachable (or set it before closing) and "
                    "air over its inductor and chip."),
    "l298n_driver": ("power", "Electrical Parts/Motor Drivers/L298N/L298N.step",
                     "L298N dual motor driver", E,
                     el("gpio", None, "dual H-bridge: two DC motors or one stepper"),
                     "Dual H-bridge motor driver board with a heatsink.",
                     "Its heatsink gets hot: vents over it and no wall touching it. Leave its "
                     "screw terminals reachable."),
    "dhb12_driver": ("power", "Electrical Parts/Motor Drivers/DHB12/DHB12.stp",
                     "DHB12 motor driver", E, el("gpio"),
                     "DC motor driver board.",
                     "Leave its terminals reachable and air over it."),
    "dc_jack_2_1mm": ("power", "Electronics Parts/Connectors/power-connectors/jack_DC_2.1mm_PCB.step",
                      "DC barrel jack, 2.1 mm (PCB)", P, el("power"),
                      "Power socket for a 2.1 mm barrel plug.",
                      "Its mouth must sit at a wall with a round opening and room outside "
                      "for the plug."),
    "fuse_mf_r500": ("power", "Electronics Parts/Fuses/THT/fuse-MF-R500.step",
                     "Resettable fuse, Bourns MF-R500", P, el("power"),
                     "Polymer PTC resettable fuse.", ""),
    "irm60_psu": ("power", "Electrical Parts/Power Supplies/IRM-60 ST series power supply/IRM-60 ST power supply.step",
                  "Mean Well IRM-60 AC-DC module", P,
                  el("power", None, "MAINS input (AC); low-voltage DC output"),
                  "Encapsulated 60 W mains-to-DC power module.",
                  "MAINS VOLTAGE: only for a design whose maker knows mains safety. Fully "
                  "enclosed, no openings a finger or tool can reach live parts through, a "
                  "proper strain-relieved mains inlet, and the low-voltage side kept apart."),
    "switching_psu": ("power", "Electrical Parts/Power Supplies/Switching power supply/Switching power supply.step",
                      "Switching power supply (enclosed)", P,
                      el("power", None, "MAINS input (AC); DC output"),
                      "Enclosed mains-to-DC power supply with screw terminals.",
                      "MAINS VOLTAGE: cover its terminal block, keep its vents open, and use a "
                      "proper mains inlet with strain relief."),
    # -------------------------------------------------------------- controls
    "push_button_22mm_red": ("controls", "Electrical Parts/Push buttons/Red Push-button - 22 mm.step",
                             "Panel push button, 22 mm (red)", E, el("gpio"),
                             "Industrial panel push button for a 22 mm hole.",
                             "It mounts through a 22 mm panel hole (about 22.3 mm) in a wall "
                             "no thicker than its thread allows; its contact block hangs "
                             "behind the wall and needs room."),
    "push_button_22mm_green": ("controls", "Electrical Parts/Push buttons/Green Push-button - 22 mm.step",
                               "Panel push button, 22 mm (green)", E, el("gpio"),
                               "Industrial panel push button for a 22 mm hole.",
                               "It mounts through a 22 mm panel hole; its contact block needs "
                               "room behind the wall."),
    "emergency_stop_22mm": ("controls", "Electrical Parts/Push buttons/Emergency stop mushroom head push-button - 22 mm.step",
                            "Emergency-stop button, 22 mm", E, el("gpio"),
                            "Red mushroom-head emergency-stop button for a 22 mm hole.",
                            "Put it where a hand finds it at once, on top or the front, "
                            "nothing round it to catch; 22 mm panel hole."),
    "cherry_mx_switch": ("controls", "Electronics Parts/Buttons/THT/cherry-mx-basic.step",
                         "Cherry MX key switch", E, el("gpio"),
                         "Mechanical keyboard switch.",
                         "It clips into a 14 mm square plate hole in a 1.5 mm plate; a key "
                         "cap goes on its stem."),
    "tactile_button": ("controls", "Electronics Parts/Buttons/THT/pushbutton-mini.step",
                       "Tactile push button (PCB)", E, el("gpio"),
                       "Small through-hole tactile switch.",
                       "Bring a plunger or a flexible button in the case down onto it; "
                       "leave a little travel."),
    "tactile_button_right_angle": ("controls", "Electronics Parts/Buttons/THT/pushbutton-right-angle.step",
                                   "Tactile push button, right angle (PCB)", E, el("gpio"),
                                   "Side-pressed tactile switch for a board edge.",
                                   "Its plunger faces sideways: put it at a wall with a "
                                   "button or opening in front."),
    "rocker_switch_round": ("controls", "Electronics Parts/Switch/Box/RoundRockerSwitch2Pins.step",
                            "Round rocker switch (2 pins)", P, el("power"),
                            "Snap-in round on/off rocker switch.",
                            "It snaps into a round panel hole the size of its body; leave room "
                            "behind for its two terminals."),
    "slide_switch": ("controls", "Electronics Parts/Switch/THT/slide-sw-spdt.step",
                     "Slide switch, SPDT (PCB)", E, el("gpio"),
                     "Small slide switch.",
                     "Its lever needs a slot in the wall a little longer than its travel."),
    "toggle_switch_1p2t": ("controls", "Electronics Parts/Switch/Mini toggle switch 1P2T/Interuptor conmutador 1P2T PCB.step",
                           "Mini toggle switch, 1P2T", E, el("gpio"),
                           "Small toggle switch.",
                           "Mount it through a panel hole by its threaded bushing and nut."),
    "microswitch_lever": ("controls", "Electronics Parts/Switch/Limit switch/Microswitch_SPDT_Vertical.step",
                          "Microswitch with lever (SPDT)", E, el("gpio"),
                          "Snap-action limit switch with a lever.",
                          "Mount it by its two holes where the moving part presses the lever; "
                          "leave over-travel."),
    "endstop_makerbot": ("controls", "Electrical Parts/Endstop/endstop-v1-2-makerbot.step",
                         "Mechanical endstop board (MakerBot v1.2)", E, el("gpio"),
                         "Microswitch endstop on a small board, as on 3D printers.",
                         "Mount it by its holes where the moving part presses the lever."),
    "rotary_encoder": ("controls", "Electronics Parts/Rotatory encoders/rotatory-encoder.step",
                       "Rotary encoder with push switch", E, el("gpio"),
                       "Rotary encoder knob shaft with a push switch.",
                       "Its threaded bushing mounts through a panel hole with its nut; a knob "
                       "goes on the shaft outside."),
    "potentiometer": ("controls", "Electronics Parts/Potentiometer/Potentiometer.step",
                      "Potentiometer", E, el("analog"),
                      "Rotary potentiometer.",
                      "Its bushing mounts through a panel hole with its nut; a knob goes on "
                      "the shaft outside."),
    # -------------------------------------------------------------- displays
    "led_5mm": ("displays", "Electronics Parts/LEDs/led-5mm.step", "LED, 5 mm", E, el("gpio"),
                "Through-hole 5 mm LED.",
                "Its dome can poke through a 5 mm hole, or sit behind a light pipe or a "
                "thin diffuser."),
    "led_3mm": ("displays", "Electronics Parts/LEDs/led-3mm-short.step", "LED, 3 mm", E, el("gpio"),
                "Through-hole 3 mm LED.", "Through a 3 mm hole, or behind a light pipe."),
    "rgb_led_5mm": ("displays", "Electronics Parts/LEDs/RGB-LED-5mm.step", "RGB LED, 5 mm", E,
                    el("gpio"), "Through-hole 5 mm RGB LED (four legs).",
                    "Behind a diffuser the colours mix; through a hole they show apart."),
    "led_bargraph": ("displays", "Electronics Parts/LEDs/bargraph.step", "LED bar graph", E,
                     el("gpio"), "Ten-segment LED bar graph.",
                     "A window over its face; nothing in front of the segments."),
    "buzzer": ("displays", "Electronics Parts/Buzzers/Buzzer.step", "Buzzer", E, el("gpio"),
               "Small round buzzer.",
               "Sound must get out: a hole or a few small holes over its opening."),
    "seven_segment": ("displays", "Electronics Parts/Displays/Display 7 segmentos/Archivos/Display 7 segmentos.step",
                      "7-segment LED display", E, el("gpio"),
                      "One-digit 7-segment LED display.",
                      "A window or a tinted panel over its face."),
    "lcd_20x4": ("displays", "Electronics Parts/Displays/LCD/lcd-4x20-backlight.step",
                 "LCD, 20 × 4 characters (backlit)", E, el("other"),
                 "Character LCD module, four lines of 20.",
                 "A window the size of its viewing area in the front; mount the board by its "
                 "four corner holes behind the wall."),
    "tft_2_4in": ("displays", "Electronics Parts/Displays/TFT/2-4_tft_spi_240x320.step",
                  "TFT display, 2.4 in, 240 × 320 (SPI)", E, el("spi"),
                  "Colour TFT display on a carrier board.",
                  "A window over the screen area only; mount the board by its holes behind "
                  "the wall."),
    "tft_3_5in_rpi": ("displays", "Electronics Parts/Displays/TFT/3.5_RPi_tft_display_spi_480x320.step",
                      "TFT display, 3.5 in, 480 × 320, for Raspberry Pi (SPI)", E, el("spi"),
                      "Colour TFT display that plugs onto a Raspberry Pi's header.",
                      "A window over the screen; it sits on the Pi's header, so design the two "
                      "together."),
    # ------------------------------------------------------------ connectors
    "usb_b_jack": ("connectors", "Electronics Parts/Connectors/USB-connectors/USB-2_0-type-B-jack-PCB.step",
                   "USB-B socket (PCB)", E, el("usb"), "USB 2.0 type-B socket.",
                   "Its mouth at a wall with an opening a little larger than the plug, and "
                   "room outside for the plug."),
    "usb_a_dual": ("connectors", "Electronics Parts/Connectors/USB-connectors/USB-2_0-type-A-Dual-Stacked-jack-PCB.step",
                   "USB-A socket, dual stacked (PCB)", E, el("usb"), "Two stacked USB 2.0 type-A sockets.",
                   "Its mouths at a wall with an opening round both."),
    "usb_micro_b": ("connectors", "Electronics Parts/Connectors/USB-connectors/smd/USB-micro-B.step",
                    "Micro-USB socket", E, el("usb"), "USB Micro-B socket.",
                    "Its mouth at a wall; the opening must clear the plug's overmould, not "
                    "only its metal."),
    "rj45_jack": ("connectors", "Electronics Parts/Connectors/Ethernet-connectors/rj45-ethernet-PCB-with-leds.step",
                  "RJ45 Ethernet socket with LEDs", E, el("other"), "Ethernet socket with status LEDs.",
                  "Its mouth at a wall with room for the plug's latch to be pressed."),
    "hdmi_jack": ("connectors", "Electronics Parts/Connectors/HDMI-connectors/hdmi-connector.step",
                  "HDMI socket", E, el("other"), "Full-size HDMI socket.",
                  "Its mouth at a wall with an opening that clears the plug's overmould."),
    "audio_jack_3_5mm": ("connectors", "Electronics Parts/Connectors/Audio-connectors/3-5mm-audio-jack.step",
                         "Audio jack, 3.5 mm", E, el("other"), "3.5 mm audio socket.",
                         "Its mouth at a wall with a round opening."),
    "terminal_block_2": ("connectors", "Electronics Parts/Connectors/power-connectors/pcb-terminal-block-female-1x2.step",
                         "Screw terminal block, 2 way", P, el("power"), "PCB screw terminal block.",
                         "Its screws must be reachable with a screwdriver and its wire entries "
                         "face an opening or the open case."),
    "terminal_block_4": ("connectors", "Electronics Parts/Connectors/power-connectors/pcb-terminal-block-female-1x4.step",
                         "Screw terminal block, 4 way", P, el("power"), "PCB screw terminal block.",
                         "Its screws reachable, its wire entries facing an opening."),
    "micro_sd_card": ("connectors", "Computing/Storage/SD/Generic_MICRO_SD_card.step",
                      "Micro-SD card", E, None, "A micro-SD card (the card, for a slot).",
                      "A slot in the wall in line with the card socket, with room for a "
                      "fingertip to push it in and out."),
    # ------------------------------------------------------------ R910 more
    "ramps_14": ("boards", "Computing/SingleBoardComputers/Reprap/ramps-1_4.step",
                 "RAMPS 1.4 (Arduino Mega shield)", E,
                 el("other", 12, "plugs onto an Arduino Mega; 12 V power input",
                    "sockets for 5 stepper drivers; screw terminals for power, heaters"),
                 "3D-printer controller shield that plugs onto an Arduino Mega 2560.",
                 "It sits on top of an Arduino Mega: design the two together. Its power "
                 "terminals and the stepper drivers need air; leave room above for the "
                 "drivers' heatsinks."),
    "nano_io_shield": ("boards", "Computing/SingleBoardComputers/Shields/nano_expansion_shield.step",
                       "Arduino Nano I/O expansion shield", E, el("other", None, "takes an Arduino Nano"),
                       "Carrier board for an Arduino Nano with its pins brought out to "
                       "3-pin headers.",
                       "The Nano plugs in on top; its USB socket must stay reachable. Leave "
                       "room above the 3-pin rows for servo and sensor plugs."),
    "reprap_smart_lcd": ("displays", "Computing/SingleBoardComputers/Shields/smart-lcd-ramps.step",
                         "RepRap smart LCD controller (20 × 4)", E,
                         el("other", None, None, "two 2 × 5 ribbon sockets"),
                         "20 × 4 character LCD with a click knob, buzzer and SD-card slot, "
                         "for RAMPS.",
                         "A front-panel window over the LCD, a hole for the knob's shaft, a "
                         "slot in line with the SD card, and room behind for the two ribbon "
                         "cables."),
    "bus_pirate": ("boards", "Computing/SingleBoardComputers/Shields/bus-pirate.step",
                   "Bus Pirate", E, el("usb"),
                   "Small USB tool board for talking to I²C, SPI and serial devices.", ""),
    "nema23_stepper": ("motors", "Electrical Parts/Motors/Stepper/NEMA/NEMA_23_with_connector.step",
                       "NEMA 23 stepper motor", M, el("other", None, None, "connector on the body"),
                       "Large stepper motor (57 mm square face) with a connector.",
                       "Mount it by its four face holes on a stiff plate; leave room behind "
                       "for the connector and cable. It is heavy and can get warm."),
    "sg90_horn_1": ("motors", "Electrical Parts/Servos/SG-90/SG90-1-arm-horn.step",
                    "SG90 servo horn, 1 arm", X, None, "Single-arm horn for an SG90 servo.",
                    "It presses onto the servo's splined shaft and is held by a small "
                    "screw; leave room for it to swing."),
    "sg90_horn_2": ("motors", "Electrical Parts/Servos/SG-90/SG90-2-arms-horn.step",
                    "SG90 servo horn, 2 arms", X, None, "Two-arm horn for an SG90 servo.", ""),
    "sg90_horn_4": ("motors", "Electrical Parts/Servos/SG-90/SG90-4-arms-horn.step",
                    "SG90 servo horn, 4 arms", X, None, "Cross horn for an SG90 servo.", ""),
    "futaba_s3003_horn_round": ("motors", "Electrical Parts/Servos/Futaba3003/Futaba3003-rounded-horn.stp",
                                "Futaba S3003 servo horn, round", X, None,
                                "Round horn (disc) for a Futaba S3003 servo.", ""),
    "futaba_s3003_horn_4": ("motors", "Electrical Parts/Servos/Futaba3003/Futaba3003-4-arms-horn.step",
                            "Futaba S3003 servo horn, 4 arms", X, None,
                            "Cross horn for a Futaba S3003 servo.", ""),
    "stepper_28byj48_horn": ("motors", "Electrical Parts/Motors/Stepper/28BYJ-48/28BYJ-48_2_arms_horn.step",
                             "28BYJ-48 horn, 2 arms", X, None,
                             "Two-arm horn for the 28BYJ-48 stepper's flatted shaft.", ""),
    "stepper_28byj48_gear": ("motors", "Electrical Parts/Motors/Stepper/28BYJ-48/28BYJ-48_gear_horn.step",
                             "28BYJ-48 gear", X, None,
                             "Spur gear for the 28BYJ-48 stepper's flatted shaft.", ""),
    "hotend_mk8": ("mechanical", "Electrical Parts/Hotend/MK8.step",
                   "3D-printer hotend, MK8 style", X, None,
                   "MK8-style extruder hotend (heater block, nozzle, heat break).",
                   "It runs at printing temperature: keep plastic well away from the heater "
                   "block and give its cooling fins a fan."),
    "hotend_jhead": ("mechanical", "Electrical Parts/Hotend/j-head.step",
                     "3D-printer hotend, J-head", X, None, "J-head style hotend.",
                     "Held by its groove mount; keep plastic away from the heater block."),
    "battery_sla_12v_7ah": ("power", "Electrical Parts/Batteries/yuasa_np7_12/Yuasa_NP7-12_F1.step",
                            "Lead-acid battery 12 V 7 Ah (Yuasa NP7-12)", P,
                            el("power", 12, None, "F1 (4.8 mm) spade terminals"),
                            "Sealed lead-acid battery, 12 V, 7 Ah.",
                            "It is heavy (over 2 kg): carry it on the base, strapped or boxed "
                            "in so it cannot shift, with its terminals covered."),
    "mcb_din": ("power", "Electrical Parts/Breakers/Schneider_EZ9F16110_MCB/Schneider_EZ9F16110_MCB.step",
                "DIN-rail circuit breaker (Schneider EZ9F16110)", P, el("power"),
                "Single-pole miniature circuit breaker for a 35 mm DIN rail.",
                "Mains wiring belongs to a qualified electrician; in a design, it clips on "
                "a DIN rail with its lever reachable through a cut-out."),
    "trimmer_multiturn": ("controls", "Electronics Parts/Rotary resistors/rotary-resistor-M64W103KB40.step",
                          "Multi-turn trimmer potentiometer (10 kΩ)", E, el("analog"),
                          "Small multi-turn trimmer for setting a value once.",
                          "Leave its adjusting screw reachable with a small screwdriver."),
    "push_button_22mm_blue": ("controls", "Electrical Parts/Push buttons/Blue Push-button - 22 mm.step",
                              "Panel push button, 22 mm, blue", E, el("gpio"),
                              "Industrial 22 mm panel push button, blue.",
                              "It mounts through a 22.3 mm round panel hole and is held by its "
                              "ring nut; room behind the panel for its contact block."),
    "mushroom_button_22mm_red": ("controls", "Electrical Parts/Push buttons/Red mushroom head push button - 22 mm.step",
                                 "Mushroom-head push button, 22 mm, red", E, el("gpio"),
                                 "22 mm panel push button with a large mushroom head.",
                                 "22.3 mm panel hole; leave room round the head for a palm."),
    "mushroom_button_22mm_green": ("controls", "Electrical Parts/Push buttons/Green mushroom head push button - 22 mm.step",
                                   "Mushroom-head push button, 22 mm, green", E, el("gpio"),
                                   "22 mm panel push button with a large mushroom head.", ""),
    "mushroom_button_22mm_black": ("controls", "Electrical Parts/Push buttons/Black mushroom head push button - 22 mm.step",
                                   "Mushroom-head push button, 22 mm, black", E, el("gpio"),
                                   "22 mm panel push button with a large mushroom head.", ""),
    "rocker_switch_round_3pin": ("controls", "Electronics Parts/Switch/Box/RoundRockerSwitch3Pins.step",
                                 "Round rocker switch, 3 pins", E, el("power"),
                                 "Round panel rocker switch with three pins.",
                                 "It snaps into a round panel hole; its pins need room behind."),
    "slide_switch_right_angle": ("controls", "Electronics Parts/Switch/THT/slide-sw-spdt-right-angle.step",
                                 "Slide switch, SPDT, right angle", E, el("gpio"),
                                 "Small slide switch whose lever sticks out sideways from the board.",
                                 "Its lever comes out through a slot in the wall: a slot as "
                                 "long as the lever's travel."),
    "microswitch_lever_h": ("controls", "Electronics Parts/Switch/Limit switch/Microswitch_SPDT_Horizontal_L.step",
                            "Microswitch with lever (horizontal)", E, el("gpio"),
                            "Lever microswitch lying flat on a board.", ""),
    "led_3mm_long": ("displays", "Electronics Parts/LEDs/led-3mm-long.step", "LED, 3 mm (long legs)", E,
                     el("gpio"), "3 mm through-hole LED.",
                     "A 3.1 mm hole in the wall shows it, or a light pipe."),
    "terminal_block_6": ("connectors", "Electronics Parts/Connectors/power-connectors/pcb-terminal-block-female-1x6.step",
                         "Screw terminal block, 6 way", P, el("power"), "PCB screw terminal block.",
                         "Its screws reachable, its wire entries facing an opening."),
    "usb_mini_b": ("connectors", "Electronics Parts/Connectors/USB-connectors/mini-usb-b-female-smd.step",
                   "Mini-USB socket", E, el("usb"), "USB Mini-B socket.",
                   "Its mouth at a wall; the opening must clear the plug's overmould."),
    "sd_card": ("connectors", "Computing/Storage/SD/Generic_SD_card.step",
                "SD card (full size)", E, None, "A full-size SD card (the card, for a slot).",
                "A slot in the wall in line with the card socket, with fingertip room."),
    "dupont_housing_1x3": ("connectors", "Electronics Parts/Connectors/dupont-connectors/dupont-2_54mm-female-conn-1x3.step",
                           "Jumper-wire plug, 3 way (2.54 mm)", E, el("other"),
                           "Female DuPont-style housing for 2.54 mm pins, 3 ways.",
                           "It plugs straight onto pins: leave room above them for the "
                           "housing and the wires bending away."),
    "dupont_housing_1x4": ("connectors", "Electronics Parts/Connectors/dupont-connectors/dupont-2_54mm-female-conn-1x4.step",
                           "Jumper-wire plug, 4 way (2.54 mm)", E, el("other"),
                           "Female DuPont-style housing for 2.54 mm pins, 4 ways.", ""),
    "pin_header_1x4": ("connectors", "Electronics Parts/Headers/2.54mm-pitch/male/straight/1x4-male-pin-header.step",
                       "Pin header 1 × 4 (2.54 mm)", E, el("other"),
                       "Straight male pin header, 4 pins.", ""),
    "pin_header_female_1x8": ("connectors", "Electronics Parts/Headers/2.54mm-pitch/female/1x8-female-pin-header.step",
                              "Socket header 1 × 8 (2.54 mm)", E, el("other"),
                              "Female socket header, 8 ways.", ""),
    "box_header_2x5": ("connectors", "Electronics Parts/Headers/2.54mm-pitch/male/box/2x5-pin-box-header-male-right-angle.step",
                       "Box header 2 × 5, right angle (2.54 mm)", E, el("other"),
                       "Shrouded 10-pin header for a ribbon cable, at right angles.",
                       "The ribbon plug comes in sideways: room at the board edge for it."),
    "mosfet_to220": ("power", "Electronics Parts/Transistors/mosfet-P55NF06L.step",
                     "MOSFET STP55NF06L (TO-220)", P,
                     el("power", None, "N-channel, logic-level gate"),
                     "N-channel power MOSFET in a TO-220 package.",
                     "For heavy loads it needs a heatsink on its tab, and air."),
    # ------------------------------------------------------------ mechanical
    "heatsink_19mm": ("mechanical", "Electronics Parts/Heatsinks/heat-sink-19x19x5mm.step",
                      "Heatsink, 19 × 19 × 5 mm", X, None, "Small finned heatsink.",
                      "Air must pass through its fins: vents in line with them."),
    "nema17_bracket": ("mechanical", "Electrical Parts/Motors/Stepper/NEMA/Nema-17_Mount_Bracket/Nema-17_MountBracket.step",
                       "NEMA 17 mounting bracket", X, None, "L bracket for a NEMA 17 motor.", ""),
    "bearing_kp08": ("mechanical", "Mechanical Parts/Mountings/KP08/KP08.step",
                     "Pillow-block bearing KP08 (8 mm)", X, None,
                     "Cast pillow-block bearing for an 8 mm shaft, two bolt holes.",
                     "Bolt it down by its two slots on a flat face; the shaft passes through "
                     "and is locked by the grub screws in the collar."),
    "bearing_kfl08": ("mechanical", "Mechanical Parts/Mountings/KFL08/KFL08.step",
                      "Flange bearing KFL08 (8 mm)", X, None,
                      "Two-bolt flange bearing for an 8 mm shaft.",
                      "Bolt it flat against a wall by its two holes; the shaft passes through "
                      "the wall, so the wall needs a hole larger than the bearing's boss."),
    "bearing_608zz": ("mechanical", "Mechanical Parts/Bearings/608ZZ_Ball_Bearing.step",
                      "Ball bearing 608ZZ (8 × 22 × 7 mm)", X, None,
                      "Shielded deep-groove ball bearing: 8 mm bore, 22 mm outside, 7 mm wide.",
                      "Press it into a printed bore a little under 22 mm, or hold it with a "
                      "shoulder and a cap; only the inner ring turns with the shaft."),
    "bearing_623zz": ("mechanical", "Mechanical Parts/Bearings/623ZZ_Ball_Bearing.step",
                      "Ball bearing 623ZZ (3 × 10 × 4 mm)", X, None,
                      "Small shielded ball bearing: 3 mm bore, 10 mm outside, 4 mm wide.",
                      "Often used as a belt idler on an M3 screw; give it washers on both "
                      "sides so only the inner ring is clamped."),
    "bearing_f623zz": ("mechanical", "Mechanical Parts/Bearings/F623ZZ_Ball_Bearing.stp",
                       "Flanged ball bearing F623ZZ (3 mm)", X, None,
                       "Small flanged ball bearing for a 3 mm shaft.",
                       "Two face to face, flanges outward, make a belt idler on an M3 screw."),
    "bearing_624zz": ("mechanical", "Mechanical Parts/Bearings/624ZZ_Ball_Bearing.stp",
                      "Ball bearing 624ZZ (4 × 13 × 5 mm)", X, None,
                      "Shielded ball bearing: 4 mm bore, 13 mm outside, 5 mm wide.", ""),
    "bearing_6201": ("mechanical", "Mechanical Parts/Bearings/Ball Bearings/6201-2RS_Ball_Bearing.step",
                     "Ball bearing 6201-2RS (12 × 32 × 10 mm)", X, None,
                     "Sealed ball bearing: 12 mm bore, 32 mm outside, 10 mm wide.", ""),
    "bearing_6803": ("mechanical", "Mechanical Parts/Bearings/Ball Bearings/6803-2RS_Ball_Bearing.step",
                     "Thin ball bearing 6803-2RS (17 × 26 × 5 mm)", X, None,
                     "Thin-section sealed ball bearing: 17 mm bore, 26 mm outside, 5 mm wide.",
                     "Its large bore lets cables or a hollow shaft pass through a turntable."),
    "lm8uu": ("mechanical", "Mechanical Parts/Bearings/linear_bearings/LM8uu.stp",
              "Linear bearing LM8UU (8 mm rod)", X, None,
              "Linear ball bushing for an 8 mm smooth rod (15 mm outside, 24 mm long).",
              "Hold it in a printed clamp or a snug bore; it slides along a hardened 8 mm "
              "rod, so the rod must be straight and the two ends of a pair in line."),
    "lm10uu": ("mechanical", "Mechanical Parts/Bearings/linear_bearings/LM10uu.step",
               "Linear bearing LM10UU (10 mm rod)", X, None,
               "Linear ball bushing for a 10 mm smooth rod.", ""),
    "lm12uu": ("mechanical", "Mechanical Parts/Bearings/linear_bearings/LM12uu.step",
               "Linear bearing LM12UU (12 mm rod)", X, None,
               "Linear ball bushing for a 12 mm smooth rod.", ""),
    "sc8uu": ("mechanical", "Mechanical Parts/Mountings/SC8UU/SC8UU.step",
              "Linear slide block SC8UU (8 mm rod)", X, None,
              "Aluminium block holding an LM8UU bearing, with four tapped holes on top.",
              "Screw the moving plate onto its four top holes; two blocks per rod."),
    "sk08": ("mechanical", "Mechanical Parts/Mountings/SK08/SK08-SK08.step",
             "Rod support SK08 (8 mm)", X, None,
             "Clamp that holds the end of an 8 mm smooth rod, bolted from below.",
             "One at each end of each rod, bolted to a flat base, the two in line."),
    "mgn12_rail": ("mechanical", "Mechanical Parts/Bearings/linear_bearings/LinearSlide-MGN12-Rail.step",
                   "Linear rail MGN12 (section)", X, None,
                   "12 mm miniature linear guide rail (a short section).",
                   "Screw it down along a flat, straight face; the real rail is cut to the "
                   "length you need."),
    "mgn12h": ("mechanical", "Mechanical Parts/Bearings/linear_bearings/LinearSlide-MGN12H.step",
               "Linear carriage MGN12H", X, None,
               "Long carriage for an MGN12 rail, four tapped holes on top.", ""),
    "mgn9_rail": ("mechanical", "Mechanical Parts/Bearings/linear_bearings/LinearSlide-MGN9-Rail.step",
                  "Linear rail MGN9 (section)", X, None,
                  "9 mm miniature linear guide rail (a short section).", ""),
    "mgn9h": ("mechanical", "Mechanical Parts/Bearings/linear_bearings/LinearSlide-MGN9H.step",
              "Linear carriage MGN9H", X, None,
              "Long carriage for an MGN9 rail.", ""),
    "t8_flange_nut": ("mechanical", "Mechanical Parts/Mountings/T8_screw_nut/Flange_nut/T8_Flange_nut.step",
                      "T8 lead-screw flange nut", X, None,
                      "Brass flange nut for a T8 lead screw.",
                      "Screw its flange to the moving part; leave clearance round the lead "
                      "screw so it is not forced off-axis."),
    "t8_antibacklash_nut": ("mechanical", "Mechanical Parts/Mountings/T8_screw_nut/Anti_backlash_nut/T8_antibacklash_nut.step",
                            "T8 anti-backlash nut", X, None,
                            "Spring-loaded nut for a T8 lead screw that takes up play.", ""),
    "t8_bracket": ("mechanical", "Mechanical Parts/Mountings/T8_housing_bracket/T8_housing_bracket.step",
                   "T8 lead-screw end bracket", X, None,
                   "Bracket that carries the end of a T8 lead screw.", ""),
    "coupler_5x8": ("mechanical", "Mechanical Parts/Fasteners/Shaft Couplers & Dowel Pins/Zaxis_coupling_5x8mm.step",
                    "Shaft coupler, 5 mm to 8 mm", X, None,
                    "Flexible coupler joining a 5 mm motor shaft to an 8 mm lead screw.",
                    "The two shafts must be in line; leave room round it to tighten its "
                    "grub screws."),
    "coupler_4x3": ("mechanical", "Mechanical Parts/Fasteners/Shaft Couplers & Dowel Pins/ShaftCoupler_4mm_to_3mm_setscrew_M3.step",
                    "Shaft coupler, 4 mm to 3 mm", X, None,
                    "Rigid coupler joining a 4 mm and a 3 mm shaft, M3 set screws.", ""),
    "gt2_pulley_20t": ("mechanical", "Mechanical Parts/Pulleys/GT2_20T_Smooth_5mm_Bore.step",
                       "GT2 pulley, 20 teeth, 5 mm bore", X, None,
                       "Timing-belt pulley for a 6 mm GT2 belt, for a 5 mm motor shaft.",
                       "It goes on a NEMA 17 shaft; the belt must run square to it, in line "
                       "with the idler at the other end."),
    "gt2_pulley_16t": ("mechanical", "Mechanical Parts/Pulleys/GT2_16T.step",
                       "GT2 pulley, 16 teeth", X, None,
                       "Small timing-belt pulley for a GT2 belt.", ""),
    "hex_coupler_12mm": ("mechanical", "Mechanical Parts/Wheels/Wheel-RC-1:8-17mm-hex/hex_coupler/Hex_Coupler_6mm_12hex_18L.step",
                         "Wheel hex coupler, 12 mm hex, 6 mm shaft", X, None,
                         "Hub that adapts a 6 mm shaft to a wheel's 12 mm hex.", ""),
    "rc_wheel_1_8": ("mechanical", "Mechanical Parts/Wheels/Wheel-RC-1:8-17mm-hex/Wheel-RC-1:8-17mm-hex.step",
                     "RC car wheel, 1:8 scale (17 mm hex)", W, None,
                     "Large RC car wheel with a 17 mm hex hub.",
                     "It needs a 17 mm hex hub on its axle and clearance all round for the "
                     "tyre to turn (and to steer, on a steered axle)."),
    "cable_chain_link": ("mechanical", "Mechanical Parts/cable-chain-links/cable-chain-link-25_5x16x12_5mm.step",
                         "Cable chain link", X, None,
                         "One link of a drag chain that guides cables to a moving part.",
                         "A chain is many links; leave room for its bend radius along the "
                         "whole travel."),
    "heatsink_8mm": ("mechanical", "Electronics Parts/Heatsinks/heat-sink-8x6x5.step",
                     "Heatsink, 8 × 6 × 5 mm", X, None, "Tiny stick-on heatsink.",
                     "Air must reach its fins."),
    "cabinet_lock": ("mechanical", "Industrial Design/Locks/cabinet_lock_40x42mm.step",
                     "Cabinet cam lock, 40 × 42 mm", X, None,
                     "Small key-operated cabinet lock.",
                     "It mounts through a door or lid; the cam must swing behind the frame "
                     "inside."),
    # ------------------------------------------------------------- hardware
    "screw_m2x6": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M2x6 ISO4762 8,8 A2K.step",
                   "Socket head screw M2 × 6", X, None,
                   "ISO 4762 hex socket head cap screw, M2, 6 mm long.",
                   "Clearance hole 2.4 mm; 1.5 mm hex key. Into plastic, use a 1.6 mm pilot "
                   "hole or a heat-set insert."),
    "screw_m2x10": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M2x10 ISO4762 8,8 A2K.step",
                    "Socket head screw M2 × 10", X, None,
                    "ISO 4762 hex socket head cap screw, M2, 10 mm long.",
                    "Clearance hole 2.4 mm; 1.5 mm hex key."),
    "screw_m3x6": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M3x6 ISO4762 8,8 A2K.step",
                   "Socket head screw M3 × 6", X, None,
                   "ISO 4762 hex socket head cap screw, M3, 6 mm long.",
                   "Clearance hole 3.4 mm; head 5.5 mm across, 3 mm tall (counterbore about "
                   "6 mm); 2.5 mm hex key. Into plastic, use an M3 heat-set insert or a nut "
                   "trap."),
    "screw_m3x8": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M3x8 ISO4762 8,8 A2K.step",
                   "Socket head screw M3 × 8", X, None,
                   "ISO 4762 hex socket head cap screw, M3, 8 mm long.",
                   "Clearance hole 3.4 mm; counterbore about 6 mm; 2.5 mm hex key."),
    "screw_m3x10": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M3x10 ISO4762 8,8 A2K.step",
                    "Socket head screw M3 × 10", X, None,
                    "ISO 4762 hex socket head cap screw, M3, 10 mm long.",
                    "Clearance hole 3.4 mm; counterbore about 6 mm; 2.5 mm hex key."),
    "screw_m3x12": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M3x12 ISO4762 8,8 A2K.step",
                    "Socket head screw M3 × 12", X, None,
                    "ISO 4762 hex socket head cap screw, M3, 12 mm long.",
                    "Clearance hole 3.4 mm; counterbore about 6 mm; 2.5 mm hex key."),
    "screw_m3x16": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M3x16 ISO4762 8,8 A2K.step",
                    "Socket head screw M3 × 16", X, None,
                    "ISO 4762 hex socket head cap screw, M3, 16 mm long.",
                    "Clearance hole 3.4 mm; counterbore about 6 mm; 2.5 mm hex key."),
    "screw_m3x20": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M3x20 ISO4762 8,8 A2K.step",
                    "Socket head screw M3 × 20", X, None,
                    "ISO 4762 hex socket head cap screw, M3, 20 mm long.",
                    "Clearance hole 3.4 mm; counterbore about 6 mm; 2.5 mm hex key."),
    "screw_m3x30": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M3x30 ISO4762 8,8 A2K.step",
                    "Socket head screw M3 × 30", X, None,
                    "ISO 4762 hex socket head cap screw, M3, 30 mm long.",
                    "Clearance hole 3.4 mm; counterbore about 6 mm; 2.5 mm hex key."),
    "screw_m4x10": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M4x10 ISO4762 8,8 A2K.step",
                    "Socket head screw M4 × 10", X, None,
                    "ISO 4762 hex socket head cap screw, M4, 10 mm long.",
                    "Clearance hole 4.5 mm; head 7 mm across (counterbore about 8 mm); 3 mm "
                    "hex key."),
    "screw_m4x20": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M4x20 ISO4762 8,8 A2K.step",
                    "Socket head screw M4 × 20", X, None,
                    "ISO 4762 hex socket head cap screw, M4, 20 mm long.",
                    "Clearance hole 4.5 mm; counterbore about 8 mm; 3 mm hex key."),
    "screw_m5x10": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M5x10 ISO4762 8,8 A2K.step",
                    "Socket head screw M5 × 10", X, None,
                    "ISO 4762 hex socket head cap screw, M5, 10 mm long (the usual 2020 "
                    "extrusion screw).",
                    "Clearance hole 5.5 mm; head 8.5 mm across (counterbore about 9.5 mm); "
                    "4 mm hex key."),
    "screw_m5x20": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO4762 Hexagon socket head cap screws/Screw M5x20 ISO4762 8,8 A2K.step",
                    "Socket head screw M5 × 20", X, None,
                    "ISO 4762 hex socket head cap screw, M5, 20 mm long.",
                    "Clearance hole 5.5 mm; counterbore about 9.5 mm; 4 mm hex key."),
    "screw_m3x10_countersunk": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/ISO10642_Hex_Socket_Countersunk_Head_Screw_M3x10.step",
                                "Countersunk screw M3 × 10", X, None,
                                "ISO 10642 hex socket countersunk screw, M3, 10 mm long.",
                                "Sits flush in a 90° countersink about 6.7 mm across over a "
                                "3.4 mm hole; good for an outside face or a lid."),
    "set_screw_m3x4": ("hardware", "Mechanical Parts/Fasteners/Bolts & Screws/Metric/DIN913_Setscrew_M3x4.step",
                       "Set screw M3 × 4", X, None,
                       "DIN 913 grub screw, M3, 4 mm long.",
                       "Locks a hub, knob or pulley on a shaft; leave a straight path for "
                       "a 1.5 mm hex key to reach it."),
    "nut_m3": ("hardware", "Mechanical Parts/Fasteners/Nuts/Metric/ISO4032_Hex_Nut_M3.step",
               "Hex nut M3", X, None, "ISO 4032 hex nut, M3 (5.5 mm across flats, 2.4 mm thick).",
               "For a printed nut trap, a hexagon about 5.8 mm across flats and 2.6 mm deep, "
               "reached from the side the screw does not come from."),
    "nut_m3_nyloc": ("hardware", "Mechanical Parts/Fasteners/Nuts/Metric/Nyloc-nut-M3.step",
                     "Nylon lock nut M3", X, None,
                     "M3 nut with a nylon insert that keeps it from working loose.",
                     "Use it on a joint that moves or vibrates (an idler, a hinge pin)."),
    "nut_m4": ("hardware", "Mechanical Parts/Fasteners/Nuts/Metric/ISO4032_Hex_Nut_M4.step",
               "Hex nut M4", X, None, "ISO 4032 hex nut, M4 (7 mm across flats).",
               "Nut trap about 7.3 mm across flats."),
    "nut_m5": ("hardware", "Mechanical Parts/Fasteners/Nuts/Metric/ISO4032_Hex_Nut_M5.step",
               "Hex nut M5", X, None, "ISO 4032 hex nut, M5 (8 mm across flats).",
               "Nut trap about 8.3 mm across flats."),
    "washer_m3": ("hardware", "Mechanical Parts/Fasteners/Washers/Metric/ISO7091_CLASS_C_M3.step",
                  "Flat washer M3", X, None, "ISO 7091 plain washer for M3.",
                  "Under a screw head or nut on plastic, it spreads the load."),
    "washer_m4": ("hardware", "Mechanical Parts/Fasteners/Washers/Metric/ISO7091_CLASS_C_M4.step",
                  "Flat washer M4", X, None, "ISO 7091 plain washer for M4.", ""),
    "washer_m5": ("hardware", "Mechanical Parts/Fasteners/Washers/Metric/ISO7091DIN126_CLASS_C_M5.step",
                  "Flat washer M5", X, None, "ISO 7091 plain washer for M5.", ""),
    "washer_m3_large": ("hardware", "Mechanical Parts/Fasteners/Washers/Metric/ISO7093DIN9021_M3FlatWasher.step",
                        "Large flat washer M3 (DIN 9021)", X, None,
                        "Wide washer for M3: spreads the load on soft or printed parts.", ""),
    "standoff_m3_12": ("hardware", "Mechanical Parts/Fasteners/Standoff/Hex-Standoff-M3-12mm-Male-Female.step",
                       "Hex standoff M3, 12 mm (male-female)", X, None,
                       "Hexagonal spacer, M3 thread on one end, M3 socket on the other.",
                       "Raises a circuit board off a base: screw it into a tapped hole, a nut "
                       "or an insert, and fix the board on top with an M3 screw."),
    "standoff_m3_15": ("hardware", "Mechanical Parts/Fasteners/Standoff/Hex-Standoff-M3-15mm-Male-Female.step",
                       "Hex standoff M3, 15 mm (male-female)", X, None,
                       "Hexagonal spacer, M3 thread on one end, M3 socket on the other.",
                       "Raises a circuit board off a base; stack them for more height."),
    "tnut_2020_m3": ("hardware", "Mechanical Parts/Fasteners/T-nuts/TNut_2020_Slot6_Sliding_M3.step",
                     "Sliding T-nut, 2020 slot, M3", X, None,
                     "Nut that slides in the 6 mm slot of a 2020 aluminium extrusion.", ""),
    "tnut_2020_m5": ("hardware", "Mechanical Parts/Fasteners/T-nuts/TNut_2020_Slot6_Sliding_M5.step",
                     "Sliding T-nut, 2020 slot, M5", X, None,
                     "Nut that slides in the 6 mm slot of a 2020 aluminium extrusion.",
                     "Slide it in from the end of the extrusion before the end is closed, or "
                     "use a drop-in T-nut."),
    "vslot_2020_50": ("hardware", "Mechanical Parts/Mountings/2020_V-slot_Al_extrusion/2020x50_V_slot_profile-Part.step",
                      "Aluminium extrusion 2020 V-slot, 50 mm", X, None,
                      "20 × 20 mm V-slot aluminium profile, a 50 mm piece (cut to length "
                      "for real).",
                      "Frames are built from it with corner brackets and M5 screws in "
                      "T-nuts; the centre bore takes an M5 tap for end screws."),
    "corner_bracket_2020": ("hardware", "Mechanical Parts/Mountings/Corner/2020_corner_bracket-Corner.step",
                            "Corner bracket for 2020 extrusion", X, None,
                            "Right-angle bracket joining two 2020 extrusions.",
                            "Fixed with M5 screws into T-nuts in each extrusion."),
    "joining_plate_l": ("hardware", "Mechanical Parts/Mountings/Joining_plate/L_shaped_5_holes-Plate.step",
                        "Joining plate, L, 5 holes (2020)", X, None,
                        "Flat L plate joining two 2020 extrusions at a corner.", ""),
    "joining_plate_t": ("hardware", "Mechanical Parts/Mountings/Joining_plate/T_shaped_5_holes-Plate.step",
                        "Joining plate, T, 5 holes (2020)", X, None,
                        "Flat T plate joining 2020 extrusions at a T.", ""),
    "gantry_plate_2020": ("hardware", "Mechanical Parts/Mountings/Gantry_plate/Gantry_plate_20mm_v_slot.step",
                          "Gantry plate for 20 mm V-slot", X, None,
                          "Plate that carries V-wheels along a 20 mm V-slot extrusion.", ""),
}


def _get_json(url):
    import urllib.request
    import simready
    req = urllib.request.Request(url, headers={"User-Agent": "Prompt2Product",
                                               "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    with urllib.request.urlopen(req, timeout=120, context=simready._ssl_context()) as r:
        return json.load(r)


_COMMITS = {}


def _commit(sha):
    if sha not in _COMMITS:
        _COMMITS[sha] = _get_json("https://api.github.com/repos/%s/commits/%s?per_page=300"
                                  % (shelf.REPO, sha))
    return _COMMITS[sha]


def authors(path, rev):
    """Who made the file, oldest first: the authors of every commit that
    added or changed its content, following it back through renames (the
    2026 reorganisation moved most parts; a pure move is not authorship).
    MEASURED 2026-10-29: without following renames, 23 of the curated parts
    named only the person who moved them."""
    names, sha = [], rev                           # oldest first
    for _hop in range(12):
        hist = _get_json("https://api.github.com/repos/%s/commits?sha=%s&path=%s&per_page=100"
                         % (shelf.REPO, sha, urllib.parse.quote(path)))
        if not hist:
            break
        hop, prev = [], None
        for c in reversed(hist):                   # this path's commits, oldest first
            det = _commit(c["sha"])
            f = next((x for x in det.get("files") or [] if x.get("filename") == path), None)
            if f is not None and f.get("status") == "renamed":
                if c is hist[-1]:
                    prev = (f.get("previous_filename"),
                            (det.get("parents") or [{}])[0].get("sha"))
                if not f.get("changes"):
                    continue                       # a pure move
            n = (c.get("commit") or {}).get("author", {}).get("name")
            if n:
                hop.append(n)
        names = hop + names                        # an earlier hop is older
        if not prev or not prev[0] or not prev[1]:
            break
        path, sha = prev
    out = []
    for n in names:
        if n not in out:
            out.append(n)
    return out


from mesh_picture import PICTURE_PX, render_picture  # noqa: E402,F401


def picture_rel(key):
    return "shelf_pictures/%s.png" % key


def refresh_pictures(only=None):
    """SHELF_MODE=pictures (SHELF_ONLY=key,key): download, mesh and draw each part's picture."""
    with open(shelf.INDEX, encoding="utf-8") as fh:
        out = json.load(fh)
    import user_parts
    tmp = tempfile.mkdtemp(prefix="shelf_pic_")
    for key, e in out["parts"].items():
        if only and key not in only:
            continue
        step = shelf.fetch(e["path"], e["git_oid"], e["bytes"],
                           os.path.join(tmp, key + os.path.splitext(e["path"])[1].lower()),
                           out["revision"])
        render_picture(user_parts.read_mesh(step), os.path.join(HERE, picture_rel(key)))
        os.remove(step)
        e["picture"] = picture_rel(key)
        print("%-28s %s" % (key, e["picture"]))
        sys.stdout.flush()
    with open(shelf.INDEX, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    print("SHELF_PICTURES=%d" % sum(1 for e in out["parts"].values() if e.get("picture")))


def refresh_authors():
    """SHELF_MODE=authors: re-read only the authors of the parts already indexed."""
    with open(shelf.INDEX, encoding="utf-8") as fh:
        out = json.load(fh)
    for key, e in out["parts"].items():
        e["authors"] = authors(e["path"], out["revision"])
        print("%-28s %s" % (key, ", ".join(e["authors"])))
        sys.stdout.flush()
    with open(shelf.INDEX, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    print("SHELF_AUTHORS=%d" % len(out["parts"]))


def main():
    # freecadcmd takes command-line words as its own options: modes come
    # by environment
    mode = os.environ.get("SHELF_MODE", "")
    if mode == "authors":
        return refresh_authors()
    if mode == "pictures":
        return refresh_pictures([k for k in os.environ.get("SHELF_ONLY", "").split(",") if k])
    rev = shelf.REVISION
    tree = _get_json("https://api.github.com/repos/%s/git/trees/%s?recursive=1"
                     % (shelf.REPO, rev))
    if tree.get("truncated"):
        raise SystemExit("the tree listing is truncated")
    blobs = {x["path"]: x for x in tree["tree"] if x["type"] == "blob"}
    out = {"source": "github.com/%s" % shelf.REPO, "revision": rev,
           "licence": shelf.LICENCE, "parts": {}}
    only = [k for k in os.environ.get("SHELF_ONLY", "").split(",") if k]
    if only:                                       # keep the others as indexed
        with open(shelf.INDEX, encoding="utf-8") as fh:
            old = json.load(fh)
        if old.get("revision") != rev:
            raise SystemExit("SHELF_ONLY needs an index at %s; do a full build" % rev)
        out["parts"] = {k: e for k, e in old["parts"].items() if k in CURATED}
    tmp = tempfile.mkdtemp(prefix="shelf_idx_")
    import user_parts
    for key, (group, path, shown, cat, elec, desc, notes) in CURATED.items():
        if only and key not in only:
            continue
        assert group in dict(shelf.GROUPS), key
        assert cat in user_parts.CATEGORIES, key
        b = blobs.get(path)
        if b is None:
            raise SystemExit("%s: %s is not in the library at %s" % (key, path, rev))
        step = shelf.fetch(path, b["sha"], b["size"],
                           os.path.join(tmp, key + os.path.splitext(path)[1].lower()), rev)
        mesh = user_parts.read_mesh(step)
        bb = mesh.BoundBox
        size = [round(bb.XLength, 2), round(bb.YLength, 2), round(bb.ZLength, 2)]
        os.remove(step)
        fc = os.path.splitext(path)[0] + ".FCStd"
        thumb = "thumbnails/" + hashlib.md5(urllib.parse.quote(fc).encode()).hexdigest() + ".png"
        e = {"group": group, "path": path, "git_oid": b["sha"], "bytes": b["size"],
             "display_name": shown, "category": cat, "description": desc,
             "agent_notes": notes, "size_mm": size, "triangles": int(mesh.CountFacets),
             "authors": authors(path, rev),
             "thumb": thumb if thumb in blobs else None}
        if elec:
            e["electrical"] = elec
        if (out["parts"].get(key) or {}).get("picture"):
            e["picture"] = out["parts"][key]["picture"]
        out["parts"][key] = e
        print("%-28s %-10s %s %s" % (key, group, size, ", ".join(e["authors"])))
        sys.stdout.flush()
    out["parts"] = {k: out["parts"][k] for k in CURATED if k in out["parts"]}
    out["count"] = len(out["parts"])
    with open(shelf.INDEX, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    print("SHELF_INDEX=%d" % len(out["parts"]))


main()
