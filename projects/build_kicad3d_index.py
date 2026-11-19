"""build_kicad3d_index - write kicad3d_index.json, the KiCad components
Prompt2Product offers, from the KiCad 3D model library at kicad3d.REVISION.

    freecadcmd projects/build_kicad3d_index.py              # full build + pictures
    KICAD_ONLY=a,b freecadcmd ...                           # (re)build only these
    KICAD_MODE=colour [KICAD_ONLY=a,b] [KICAD_SHOWCASE=<dir>] freecadcmd ...
        # redraw the pictures in the models' own colours (step_colours); with
        # KICAD_SHOWCASE also write <dir>/<key>.bin, the coloured meshes a
        # web page shows (format in write_showcase)

CURATED below is the list and everything we SAY about each model: what it
is, its pin pitch and count where the model's name settles it, notes for
the agent. Everything else is MEASURED or READ here:
  * path and git blob id from the repository tree at REVISION (GitLab's
    tree API), the byte size from the download (blob id checked);
  * size_mm and triangles from the model's own mesh (user_parts.read_mesh);
  * authors: the FILE_NAME author of the STEP header ("kicad StepUp",
    "CadQuery"... the tool or person KiCad's file names), always with the
    KiCad library contributors;
  * picture: drawn from the mesh (mesh_picture), seen from above the front.
"""
import json
import math
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kicad3d  # noqa: E402
from mesh_picture import render_picture, render_triangles  # noqa: E402

E, P = "electronics", "power"


def el(interface=None, voltage_v=None, wiring=None, connectors=None):
    d = {"interface": interface, "voltage_v": voltage_v, "wiring": wiring,
         "connectors": connectors}
    return {k: v for k, v in d.items() if v is not None}


H = "Connector_PinHeader_2.54mm.3dshapes/"
S = "Connector_PinSocket_2.54mm.3dshapes/"
J = "Connector_JST.3dshapes/"
PCB = ("A board part: it is soldered to a circuit board, so place it on the "
       "board you design around, not loose in the case.")


def _headers():
    out = {}
    for n in (2, 3, 4, 5, 6, 8):
        out["pin_header_1x%02d" % n] = (
            "connectors", H + "PinHeader_1x%02d_P2.54mm_Vertical.step" % n,
            "Pin header 1×%d, 2.54 mm, straight" % n, E,
            el(connectors="%d pins, 2.54 mm pitch" % n),
            "Straight male header, one row of %d pins at 2.54 mm (0.1 in)." % n,
            "Leave room above the pins for Dupont plugs (about 15 mm).")
    for r in ("03", "05", "10", "20"):
        out["pin_header_2x" + r] = (
            "connectors", H + "PinHeader_2x%s_P2.54mm_Vertical.step" % r,
            "Pin header 2×%d, 2.54 mm, straight" % int(r), E,
            el(connectors="%d pins in 2 rows, 2.54 mm pitch" % (2 * int(r))),
            "Straight male header, two rows of %d pins at 2.54 mm." % int(r),
            "Leave room above the pins for a plug or ribbon cable.")
    for n in (2, 3, 4, 6, 8):
        out["pin_socket_1x%02d" % n] = (
            "connectors", S + "PinSocket_1x%02d_P2.54mm_Vertical.step" % n,
            "Pin socket 1×%d, 2.54 mm, straight" % n, E,
            el(connectors="%d contacts, 2.54 mm pitch" % n),
            "Female header, one row of %d contacts at 2.54 mm: a module plugs in." % n,
            "The module plugged into it sits about 8.5 mm above the board.")
    out["pin_socket_2x20"] = (
        "connectors", S + "PinSocket_2x20_P2.54mm_Vertical.step",
        "Pin socket 2×20, 2.54 mm (Raspberry Pi HAT)", E,
        el(connectors="40 contacts in 2 rows, 2.54 mm pitch"),
        "Female 2×20 header, the Raspberry Pi GPIO size.", "")
    for n in (2, 3, 4, 5, 6):
        out["jst_xh_%d" % n] = (
            "connectors", J + "JST_XH_B%dB-XH-A_1x%02d_P2.50mm_Vertical.step" % (n, n),
            "JST XH %d-pin, 2.50 mm, vertical" % n, E,
            el(connectors="JST XH, %d pins, 2.50 mm pitch" % n),
            "JST XH board connector (B%dB-XH-A), %d pins at 2.50 mm: battery "
            "balance leads, fans, sensors." % (n, n),
            "The mating plug stands about 10 mm above the board; leave room to "
            "pull it straight up.")
    for n in (2, 3, 4, 6):
        out["jst_ph_%d" % n] = (
            "connectors", J + "JST_PH_B%dB-PH-K_1x%02d_P2.00mm_Vertical.step" % (n, n),
            "JST PH %d-pin, 2.00 mm, vertical" % n, E,
            el(connectors="JST PH, %d pins, 2.00 mm pitch" % n),
            "JST PH board connector (B%dB-PH-K), %d pins at 2.00 mm: the usual "
            "LiPo cell plug." % (n, n), "Leave room to pull the plug straight up.")
    for n in (2, 3, 4, 6):
        out["jst_sh_%d" % n] = (
            "connectors", J + "JST_SH_SM%02dB-SRSS-TB_1x%02d-1MP_P1.00mm_Horizontal.step" % (n, n),
            "JST SH %d-pin, 1.00 mm, side entry" % n, E,
            el(connectors="JST SH, %d pins, 1.00 mm pitch" % n),
            "JST SH surface-mount connector, %d pins at 1.00 mm (Qwiic / "
            "STEMMA QT use the 4-pin one)." % n,
            "The cable enters from the side, at the board edge: leave the side open.")
    for n in (2, 4, 6):
        out["molex_kk_%d" % n] = (
            "connectors", "Connector_Molex.3dshapes/Molex_KK-254_AE-6410-%02dA_1x%02d_P2.54mm_Vertical.step" % (n, n),
            "Molex KK 254, %d-pin, vertical" % n, E,
            el(connectors="Molex KK, %d pins, 2.54 mm pitch" % n),
            "Molex KK 254 friction-lock header, %d pins at 2.54 mm (fans, "
            "PC-style leads)." % n, "")
    return out


CURATED = {
    # --------------------------------------------------------------- modules
    "pico": ("modules", "Module.3dshapes/RaspberryPi_Pico.step",
             "Raspberry Pi Pico", E,
             el("usb", None, "RP2040; 3.3 V logic", "Micro-USB; castellated 2.54 mm pins"),
             "Raspberry Pi Pico microcontroller board (RP2040) with a Micro-USB socket.",
             "Leave the Micro-USB end reachable through a wall opening."),
    "pico_w": ("modules", "Module.3dshapes/RaspberryPi_Pico_W.step",
               "Raspberry Pi Pico W", E,
               el("usb", None, "RP2040 with Wi-Fi; 3.3 V logic", "Micro-USB"),
               "Raspberry Pi Pico W: the Pico with Wi-Fi and Bluetooth.",
               "Keep the antenna end (away from the USB) clear of metal; leave the "
               "Micro-USB reachable."),
    "pico_headers": ("modules", "Module.3dshapes/RaspberryPi_Pico_AddedHeaders_H2.54mm.step",
                     "Raspberry Pi Pico with headers", E,
                     el("usb", None, "RP2040; 3.3 V logic", "Micro-USB; 2 rows of 20 pins"),
                     "The Pico with pin headers soldered on, for a breadboard or socket.",
                     "Leave room under the pins for a socket or breadboard."),
    "esp32_wroom_32e": ("modules", "RF_Module.3dshapes/ESP32-WROOM-32E.step",
                        "ESP32-WROOM-32E module", E,
                        el(None, 3.3, "ESP32 with Wi-Fi and Bluetooth; 3.3 V"),
                        "Espressif ESP32-WROOM-32E Wi-Fi/Bluetooth module (the chip on "
                        "most ESP32 boards).", "Keep metal and ground copper away from "
                        "the antenna end. " + PCB),
    "esp32_s3_wroom_1": ("modules", "RF_Module.3dshapes/ESP32-S3-WROOM-1.step",
                         "ESP32-S3-WROOM-1 module", E,
                         el(None, 3.3, "ESP32-S3 with Wi-Fi and Bluetooth LE; 3.3 V"),
                         "Espressif ESP32-S3-WROOM-1 Wi-Fi/Bluetooth module.",
                         "Keep metal away from the antenna end. " + PCB),
    "esp32_c3_wroom_02": ("modules", "RF_Module.3dshapes/ESP32-C3-WROOM-02.step",
                          "ESP32-C3-WROOM-02 module", E,
                          el(None, 3.3, "ESP32-C3 with Wi-Fi and Bluetooth LE; 3.3 V"),
                          "Espressif ESP32-C3-WROOM-02 Wi-Fi/Bluetooth module.",
                          "Keep metal away from the antenna end. " + PCB),
    "esp_12e": ("modules", "RF_Module.3dshapes/ESP-12E.step", "ESP-12E (ESP8266) module", E,
                el(None, 3.3, "ESP8266 with Wi-Fi; 3.3 V"),
                "ESP-12E Wi-Fi module with the ESP8266.", "Keep metal away from the antenna. " + PCB),
    "wemos_d1_mini": ("modules", "RF_Module.3dshapes/WEMOS_D1_mini_light.step",
                      "WEMOS D1 mini", E, el("usb", None, "ESP8266 with Wi-Fi"),
                      "WEMOS D1 mini ESP8266 Wi-Fi board.",
                      "Leave its USB end reachable."),
    # ------------------------------------------------------------ connectors
    "usb_c_16p": ("connectors", "Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step",
                  "USB-C socket, 16-pin (GCT USB4105)", E, el("usb", None, None, "USB-C"),
                  "USB-C receptacle for a board edge, USB 2.0 + power (16 contacts).",
                  "Put it at the board edge and cut a 9.5 × 3.6 mm (+ clearance) slot "
                  "in the wall for the plug's overmould."),
    "usb_c_6p": ("connectors", "Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal.step",
                 "USB-C socket, power only (GCT USB4125)", E, el("power", 5, None, "USB-C"),
                 "Power-only USB-C receptacle (6 contacts, no data).",
                 "At the board edge, with a wall slot for the plug."),
    "usb_micro_b": ("connectors", "Connector_USB.3dshapes/USB_Micro-B_Molex_47346-0001.step",
                    "Micro-USB socket (Molex 47346)", E, el("usb", None, None, "Micro-USB"),
                    "Micro-USB B receptacle for a board edge.", "At the board edge, with a wall slot."),
    "usb_a": ("connectors", "Connector_USB.3dshapes/USB_A_Molex_67643_Horizontal.step",
              "USB-A socket (Molex 67643)", E, el("usb", None, None, "USB-A"),
              "USB-A receptacle, through-hole, horizontal.", "At the board edge, with a wall opening."),
    "barrel_jack": ("connectors", "Connector_BarrelJack.3dshapes/BarrelJack_CUI_PJ-063AH_Horizontal.step",
                    "DC barrel jack 2.0 mm (CUI PJ-063AH)", P, el("power", None, None, "5.5/2.0 mm barrel"),
                    "DC power jack for a 5.5 mm barrel plug with a 2.0 mm pin.",
                    "At the board edge; open the wall around the plug (about 9 mm round)."),
    "barrel_jack_21": ("connectors", "Connector_BarrelJack.3dshapes/BarrelJack_CUI_PJ-079BH_Horizontal.step",
                       "DC barrel jack 2.5 mm (CUI PJ-079BH)", P, el("power", None, None, "5.5/2.5 mm barrel"),
                       "DC power jack for a 5.5 mm barrel plug with a 2.5 mm pin.",
                       "At the board edge; open the wall around the plug."),
    "jack_35mm": ("connectors", "Connector_Audio.3dshapes/Jack_3.5mm_CUI_SJ1-3523N_Horizontal.step",
                  "3.5 mm audio jack, stereo (CUI SJ1-3523N)", E, el(None, None, None, "3.5 mm TRS"),
                  "3.5 mm stereo headphone jack, through-hole.", "At the board edge, with a 6 mm hole in the wall."),
    "rj45": ("connectors", "Connector_RJ.3dshapes/RJ45_Amphenol_RJHSE538X.step",
             "RJ45 Ethernet socket (Amphenol RJHSE538X)", E, el(None, None, None, "RJ45"),
             "Shielded RJ45 Ethernet jack.", "At the board edge, with a wall opening for the plug and its latch."),
    "microsd": ("connectors", "Connector_Card.3dshapes/microSD_HC_Hirose_DM3D-SF.step",
                "microSD card socket (Hirose DM3D)", E, el("spi", 3.3, None, "microSD"),
                "Push-push microSD card socket, surface mount.",
                "At the board edge, with a slot in the wall to insert the card."),
    "terminal_2": ("connectors", "TerminalBlock_Phoenix.3dshapes/TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal.step",
                   "Screw terminal 2-way, 5.08 mm (Phoenix MKDS)", E,
                   el(connectors="2 screw terminals, 5.08 mm pitch"),
                   "Screw terminal block, 2 ways: wires clamp in with a screwdriver.",
                   "Leave the wire entry side and the screw tops reachable."),
    "terminal_3": ("connectors", "TerminalBlock_Phoenix.3dshapes/TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal.step",
                   "Screw terminal 3-way, 5.08 mm (Phoenix MKDS)", E,
                   el(connectors="3 screw terminals, 5.08 mm pitch"),
                   "Screw terminal block, 3 ways.", "Leave the wire entry side and the screw tops reachable."),
    "idc_2x05": ("connectors", "Connector_IDC.3dshapes/IDC-Header_2x05_P2.54mm_Vertical.step",
                 "Box header 2×5 (IDC, 10-pin)", E, el(connectors="10 pins, 2.54 mm pitch, keyed"),
                 "Shrouded, keyed 10-pin header for a ribbon cable.", ""),
    "idc_2x20": ("connectors", "Connector_IDC.3dshapes/IDC-Header_2x20_P2.54mm_Vertical.step",
                 "Box header 2×20 (IDC, 40-pin)", E, el(connectors="40 pins, 2.54 mm pitch, keyed"),
                 "Shrouded, keyed 40-pin header for a ribbon cable.", ""),
    "ffc_15": ("connectors", "Connector_FFC-FPC.3dshapes/Hirose_FH12-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal.step",
               "FFC connector 15-pin, 0.5 mm (Hirose FH12)", E,
               el(connectors="15 contacts, 0.5 mm pitch flat cable"),
               "Flat flex cable connector, 15 contacts at 0.5 mm.",
               "The flat cable enters from the side: leave a slot for it."),
    # ---------------------------------------------------------------- controls
    "tact_6mm": ("controls", "Button_Switch_THT.3dshapes/SW_PUSH_6mm.step",
                 "Tactile button 6 × 6 mm", E, el("gpio", None, "2 contacts, closed while pressed"),
                 "The common 6 × 6 mm through-hole push button.",
                 "Press it through a hole in the wall with a printed cap, or leave its stem reachable."),
    "tact_6mm_h13": ("controls", "Button_Switch_THT.3dshapes/SW_PUSH_6mm_H13mm.step",
                     "Tactile button 6 × 6 mm, tall (13 mm)", E, el("gpio", None, "closed while pressed"),
                     "6 × 6 mm push button with a tall stem, to reach through a case wall.",
                     "The stem reaches through a 4 mm hole in a lid above the board."),
    "tact_12mm": ("controls", "Button_Switch_THT.3dshapes/SW_PUSH-12mm_Wuerth-430476085716.step",
                  "Tactile button 12 × 12 mm (Würth)", E, el("gpio", None, "closed while pressed"),
                  "Large 12 × 12 mm push button.", ""),
    "omron_b3f": ("controls", "Button_Switch_THT.3dshapes/SW_TH_Tactile_Omron_B3F-100x.step",
                  "Tactile button Omron B3F", E, el("gpio", None, "closed while pressed"),
                  "Omron B3F 6 × 6 mm through-hole tactile switch.", ""),
    "tact_smd": ("controls", "Button_Switch_SMD.3dshapes/SW_SPST_PTS645Sx43SMTR92.step",
                 "Tactile button 6 × 6 mm, SMD (C&K PTS645)", E, el("gpio", None, "closed while pressed"),
                 "Surface-mount 6 × 6 mm push button.", ""),
    "slide_spdt": ("controls", "Button_Switch_THT.3dshapes/SW_Slide_SPDT_Straight_CK_OS102011MS2Q.step",
                   "Slide switch SPDT (C&K OS102011)", E, el("power", None, "common pin to one of two"),
                   "Small slide switch, single pole double throw: an on/off switch.",
                   "Its lever reaches through a slot in the wall; make the slot the "
                   "travel plus 1 mm."),
    "slide_spdt_angled": ("controls", "Button_Switch_THT.3dshapes/SW_Slide_SPDT_Angled_CK_OS102011MA1Q.step",
                          "Slide switch SPDT, right angle", E, el("power", None, "common pin to one of two"),
                          "Slide switch with its lever out of the board edge.",
                          "At the board edge, with a slot in the wall for the lever."),
    "dip_switch_4": ("controls", "Button_Switch_THT.3dshapes/SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm.step",
                     "DIP switch, 4 positions", E, el("gpio", None, "4 independent switches"),
                     "Four-way DIP switch for settings.", ""),
    "dip_switch_8": ("controls", "Button_Switch_THT.3dshapes/SW_DIP_SPSTx08_Slide_9.78x22.5mm_W7.62mm_P2.54mm.step",
                     "DIP switch, 8 positions", E, el("gpio", None, "8 independent switches"),
                     "Eight-way DIP switch for settings.", ""),
    "pot_trimmer": ("controls", "Potentiometer_THT.3dshapes/Potentiometer_Bourns_3296W_Vertical.step",
                    "Trimmer potentiometer (Bourns 3296W)", E, el("analog", None, "3 pins: ends and wiper"),
                    "Multi-turn trimmer, adjusted with a small screwdriver from the top.",
                    "Leave the adjusting screw reachable, or a hole above it."),
    "pot_3386": ("controls", "Potentiometer_THT.3dshapes/Potentiometer_Bourns_3386W_Horizontal.step",
                 "Trimmer potentiometer (Bourns 3386W)", E, el("analog", None, "3 pins: ends and wiper"),
                 "Single-turn square trimmer.", ""),
    # ------------------------------------------------------------------ lights
    "led_5mm": ("lights", "LED_THT.3dshapes/LED_D5.0mm.step", "LED 5 mm", E,
                el("gpio", None, "anode (long leg) and cathode, with a series resistor"),
                "5 mm round through-hole LED.", "Shine it through a 5.2 mm hole or a thin wall."),
    "led_5mm_rgb": ("lights", "LED_THT.3dshapes/LED_D5.0mm-4_RGB.step", "LED 5 mm RGB (4 legs)", E,
                    el("gpio", None, "4 legs: red, green, blue and a common leg"),
                    "5 mm RGB LED with four legs.", "Shine it through a 5.2 mm hole."),
    "led_3mm": ("lights", "LED_THT.3dshapes/LED_D3.0mm.step", "LED 3 mm", E,
                el("gpio", None, "anode (long leg) and cathode, with a series resistor"),
                "3 mm round through-hole LED.", "Shine it through a 3.2 mm hole."),
    "led_0805": ("lights", "LED_SMD.3dshapes/LED_0805_2012Metric.step", "LED 0805 (SMD)", E,
                 el("gpio", None, "with a series resistor"), "2.0 × 1.25 mm surface-mount LED.",
                 "Light it through a light pipe or a thin (0.6 mm) wall."),
    "ws2812b": ("lights", "LED_SMD.3dshapes/LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm.step",
                "WS2812B addressable RGB LED (5050)", E,
                el("gpio", 5, "VDD, GND, DIN, DOUT: data chained LED to LED"),
                "5 × 5 mm addressable RGB LED (NeoPixel).",
                "Diffuse it with a thin wall or a light pipe."),
    "sk6812_mini": ("lights", "LED_SMD.3dshapes/LED_SK6812MINI-E_3.2x2.8mm_P1.5mm_ReverseMount.step",
                    "SK6812 MINI-E addressable LED (reverse mount)", E,
                    el("gpio", 5, "VDD, GND, DIN, DOUT"),
                    "3.2 × 2.8 mm addressable RGB LED that shines down through a board hole "
                    "(keyboard backlights).", ""),
    "seven_seg": ("lights", "Display_7Segment.3dshapes/CA56-12EWA.step",
                  "7-segment display, 4 digits 0.56 in (Kingbright CA56-12)", E,
                  el("gpio", None, "common anode, multiplexed digits"),
                  "Four-digit 0.56-inch red 7-segment LED display.",
                  "Show it through a window in the wall the size of its face."),
    "seven_seg_1": ("lights", "Display_7Segment.3dshapes/MAN71A.step",
                    "7-segment display, 1 digit 0.3 in (MAN71A)", E,
                    el("gpio", None, "common anode"), "Single 0.3-inch 7-segment LED digit.", ""),
    "oled_ssd1306": ("lights", "Display.3dshapes/Adafruit_SSD1306.step",
                     "OLED display 128×64 SSD1306 (Adafruit)", E, el("i2c", 3.3, "SSD1306 controller"),
                     "Adafruit's 0.96-inch monochrome OLED breakout (SSD1306).",
                     "Show its glass through a window the size of the active area; hold the "
                     "board by its holes, not the glass."),
    "lcd_1602": ("lights", "Display.3dshapes/WC1602A.step", "LCD 16×2 character display (WC1602A)", E,
                 el("gpio", 5, "HD44780-style parallel interface, 16 pins"),
                 "The classic 16×2 character LCD module with backlight.",
                 "Window the wall to the viewing area; mount it by its four corner holes."),
    "lcd_2004": ("lights", "Display.3dshapes/NHD-0420H1Z.step", "LCD 20×4 character display (Newhaven)", E,
                 el("gpio", 5, "HD44780-style parallel interface"),
                 "20×4 character LCD module.", "Window the wall to the viewing area."),
    # ---------------------------------------------------------------- passives
    "resistor_0207": ("passives", "Resistor_THT.3dshapes/R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.step",
                      "Resistor 1/4 W, axial (DIN0207)", E, None,
                      "The usual through-hole resistor, 6.3 mm body, lying flat.", ""),
    "resistor_0204": ("passives", "Resistor_THT.3dshapes/R_Axial_DIN0204_L3.6mm_D1.6mm_P7.62mm_Horizontal.step",
                      "Resistor 1/8 W, axial (DIN0204)", E, None,
                      "Small through-hole resistor, 3.6 mm body.", ""),
    "resistor_0207_v": ("passives", "Resistor_THT.3dshapes/R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical.step",
                        "Resistor 1/4 W, standing", E, None,
                        "Through-hole resistor standing up, leads 2.54 mm apart.", ""),
    "cap_elec_5": ("passives", "Capacitor_THT.3dshapes/CP_Radial_D5.0mm_P2.00mm.step",
                   "Electrolytic capacitor Ø5 mm", E, None,
                   "Radial electrolytic capacitor, 5 mm across (small values).",
                   "Its height depends on the value; check the datasheet's height."),
    "cap_elec_8": ("passives", "Capacitor_THT.3dshapes/CP_Radial_D8.0mm_P3.50mm.step",
                   "Electrolytic capacitor Ø8 mm", E, None,
                   "Radial electrolytic capacitor, 8 mm across.",
                   "Its height depends on the value; check the datasheet's height."),
    "cap_elec_10": ("passives", "Capacitor_THT.3dshapes/CP_Radial_D10.0mm_P5.00mm.step",
                    "Electrolytic capacitor Ø10 mm", E, None,
                    "Radial electrolytic capacitor, 10 mm across (e.g. 1000 µF / 16 V).",
                    "Its height depends on the value; check the datasheet's height."),
    "cap_disc": ("passives", "Capacitor_THT.3dshapes/C_Disc_D5.0mm_W2.5mm_P5.00mm.step",
                 "Ceramic disc capacitor Ø5 mm", E, None, "Ceramic disc capacitor (100 nF and the like).", ""),
    "crystal_hc49": ("passives", "Crystal.3dshapes/Crystal_HC49-U_Vertical.step",
                     "Crystal HC-49/U", E, None, "Quartz crystal in the tall HC-49/U can (16 MHz and the like).", ""),
    "crystal_hc49s": ("passives", "Crystal.3dshapes/Crystal_HC49-4H_Vertical.step",
                      "Crystal HC-49/S (low)", E, None, "Quartz crystal in the low HC-49/S can.", ""),
    "crystal_watch": ("passives", "Crystal.3dshapes/Crystal_C26-LF_D2.1mm_L6.5mm_Vertical.step",
                      "Watch crystal 32.768 kHz (C26)", E, None,
                      "Cylindrical 2 × 6 mm watch crystal, for a real-time clock.", ""),
    "diode_do41": ("passives", "Diode_THT.3dshapes/D_DO-41_SOD81_P10.16mm_Horizontal.step",
                   "Diode DO-41 (1N4007 size)", E, None,
                   "Rectifier diode in a DO-41 body, lying flat (1N400x).", ""),
    "diode_do35": ("passives", "Diode_THT.3dshapes/D_DO-35_SOD27_P7.62mm_Horizontal.step",
                   "Diode DO-35 (1N4148 size)", E, None, "Small-signal glass diode (1N4148).", ""),
    "diode_do201": ("passives", "Diode_THT.3dshapes/D_DO-201AD_P15.24mm_Horizontal.step",
                    "Diode DO-201AD (1N5408 / SB540 size)", E, None,
                    "Large power diode in a DO-201AD body.", ""),
    "inductor_radial": ("passives", "Inductor_THT.3dshapes/L_Radial_D10.0mm_P5.00mm_Fastron_07M.step",
                        "Inductor, radial Ø10 mm", E, None, "Radial power inductor, 10 mm across.", ""),
    # -------------------------------------------------------------------- chips
    "dip_8": ("chips", "Package_DIP.3dshapes/DIP-8_W7.62mm.step", "DIP-8 chip (NE555, ATtiny85)", E, None,
              "8-pin through-hole chip package, 0.3 in wide.", ""),
    "dip_14": ("chips", "Package_DIP.3dshapes/DIP-14_W7.62mm.step", "DIP-14 chip (74HC logic)", E, None,
               "14-pin through-hole chip package.", ""),
    "dip_16": ("chips", "Package_DIP.3dshapes/DIP-16_W7.62mm.step", "DIP-16 chip (74HC595, L293D)", E, None,
               "16-pin through-hole chip package.", ""),
    "dip_28_narrow": ("chips", "Package_DIP.3dshapes/DIP-28_W7.62mm.step", "DIP-28 narrow chip (ATmega328P)", E, None,
                      "28-pin through-hole chip, 0.3 in wide: the Arduino Uno's chip.", ""),
    "dip_40": ("chips", "Package_DIP.3dshapes/DIP-40_W15.24mm.step", "DIP-40 chip (wide)", E, None,
               "40-pin through-hole chip package, 0.6 in wide.", ""),
    "to220_v": ("chips", "Package_TO_SOT_THT.3dshapes/TO-220-3_Vertical.step",
                "TO-220 (7805 regulator, MOSFET)", E, None,
                "TO-220 power package, standing: voltage regulators, MOSFETs, transistors.",
                "It gets hot under load: leave air round it or bolt a heatsink to its tab "
                "(M3)."),
    "to220_h": ("chips", "Package_TO_SOT_THT.3dshapes/TO-220-3_Horizontal_TabDown.step",
                "TO-220, lying flat", E, None, "TO-220 power package bent flat on the board.", ""),
    "to92": ("chips", "Package_TO_SOT_THT.3dshapes/TO-92_Inline.step",
             "TO-92 (2N2222, BC547, DS18B20)", E, None,
             "Small three-leg package: transistors, small regulators, the DS18B20 sensor.", ""),
    # -------------------------------------------------------------------- power
    "holder_18650": ("power", "Battery.3dshapes/BatteryHolder_Keystone_1042_1x18650.step",
                     "18650 cell holder (Keystone 1042)", P, el("power", 3.7, "one Li-ion 18650 cell"),
                     "Board-mount holder for one 18650 lithium-ion cell.",
                     "Leave room to lift the cell out (about 70 mm long)."),
    "holder_2xaa": ("power", "Battery.3dshapes/BatteryHolder_Keystone_2462_2xAA.step",
                    "2×AA battery holder (Keystone 2462)", P, el("power", 3.0, "two AA cells in series"),
                    "Board-mount holder for two AA cells.", "Give the cells a door or a lid to change them."),
    "holder_3xaaa": ("power", "Battery.3dshapes/BatteryHolder_Keystone_2479_3xAAA.step",
                     "3×AAA battery holder (Keystone 2479)", P, el("power", 4.5, "three AAA cells in series"),
                     "Board-mount holder for three AAA cells.", "Give the cells a door to change them."),
    "holder_cr2032": ("power", "Battery.3dshapes/BatteryHolder_Keystone_3034_1x20mm.step",
                      "CR2032 coin-cell holder (Keystone 3034)", P, el("power", 3.0, "one CR2032 coin cell"),
                      "Surface-mount holder for a 20 mm coin cell (CR2032).",
                      "Leave room to slide the coin cell out."),
    "holder_cr2032_tht": ("power", "Battery.3dshapes/BatteryHolder_Keystone_1060_1x2032.step",
                          "CR2032 coin-cell holder, through-hole (Keystone 1060)", P,
                          el("power", 3.0, "one CR2032 coin cell"),
                          "Through-hole holder for a CR2032 coin cell.", ""),
    "dcdc_r78": ("power", "Converter_DCDC.3dshapes/Converter_DCDC_RECOM_R-78E-0.5_THT.step",
                 "DC-DC regulator module (RECOM R-78E, 7805 size)", P,
                 el("power", None, "3 pins: in, ground, out"),
                 "Switching regulator in a 7805 footprint, much less heat than a 7805.", ""),
    "dcdc_oki78": ("power", "Converter_DCDC.3dshapes/Converter_DCDC_Murata_OKI-78SR_Vertical.step",
                   "DC-DC regulator (Murata OKI-78SR)", P, el("power", None, "3 pins: in, ground, out"),
                   "1.5 A switching regulator in a 7805-style package.", ""),
    "fuse_holder_5x20": ("power", "Fuse.3dshapes/Fuseholder_Cylinder-5x20mm_Schurter_0031_8201_Horizontal_Open.step",
                         "Fuse holder 5 × 20 mm (Schurter OGN)", P, el("power"),
                         "Open board-mount clip holder for a 5 × 20 mm glass fuse.",
                         "Keep fingers off it at mains voltage: close the case around it."),
    "fuse_holder_blade": ("power", "Fuse.3dshapes/Fuseholder_Blade_Mini_Keystone_3568.step",
                          "Mini blade fuse holder (Keystone 3568)", P, el("power"),
                          "Board-mount holder for a mini blade (car) fuse.",
                          "Leave room to pull the fuse out."),
    # ------------------------------------------------------------------ sensors
    "dht11": ("sensors", "Sensor.3dshapes/Aosong_DHT11_5.5x12.0_P2.54mm.step",
              "DHT11 temperature & humidity sensor", E,
              el("gpio", None, "VCC, data, NC, GND (2.54 mm)"),
              "Aosong DHT11 temperature and humidity sensor.",
              "It must feel the room's air: vent the case next to it and keep it away "
              "from warm parts."),
    "vl53l1x": ("sensors", "Sensor_Distance.3dshapes/ST_VL53L1x.step",
                "VL53L1X time-of-flight distance sensor (chip)", E, el("i2c", 3.3),
                "ST VL53L1X laser distance sensor chip, up to 4 m.",
                "It looks straight out of its top: give it a clear window or hole in "
                "the wall in front of it. " + PCB),
    "sharp_gp2y0a41": ("sensors", "OptoDevice.3dshapes/Sharp_GP2Y0A41SK0F.step",
                       "Sharp GP2Y0A41 IR distance sensor (4-30 cm)", E,
                       el("analog", 5, "VCC, GND, analog out"),
                       "Sharp infrared distance sensor, 4 to 30 cm.",
                       "Both lenses look out: open the wall in front of them."),
    "tcrt5000": ("sensors", "OptoDevice.3dshapes/Vishay_TCRT5000.step",
                 "TCRT5000 reflective IR sensor", E, el("analog", None, "IR LED + phototransistor"),
                 "Reflective infrared sensor: line following, near-object detection.",
                 "Face it at the surface, a few mm away, with nothing in between."),
    "cny70": ("sensors", "OptoDevice.3dshapes/Vishay_CNY70.step", "CNY70 reflective IR sensor", E,
              el("analog", None, "IR LED + phototransistor"), "Small reflective optical sensor.",
              "Face it at the surface, 0.5 to 5 mm away."),
    "ldr_5mm": ("sensors", "OptoDevice.3dshapes/R_LDR_5.1x4.3mm_P3.4mm_Vertical.step",
                "Light-dependent resistor 5 mm (LDR)", E, el("analog", None, "2 legs, resistance falls with light"),
                "5 mm photoresistor, the usual light sensor.",
                "It must see the light: a hole or a clear window over it."),
    "itr9608": ("sensors", "OptoDevice.3dshapes/Everlight_ITR9608-F.step",
                "Slotted opto switch (Everlight ITR9608)", E, el("gpio", None, "IR LED across a slot"),
                "Fork-shaped light barrier: something in the slot breaks the beam (end stops, "
                "encoders).", "Leave the slot open for the flag that passes through."),
    "mic_mems": ("sensors", "Sensor_Audio.3dshapes/Knowles_SPH0645LM4H-6_3.5x2.65mm.step",
                 "MEMS microphone I2S (Knowles SPH0645)", E, el("other", 3.3, "I2S digital audio"),
                 "Tiny digital MEMS microphone (bottom port).",
                 "The sound hole is under it, through the board: open the case under "
                 "the hole. " + PCB),
    "buzzer_12mm": ("sensors", "Buzzer_Beeper.3dshapes/Buzzer_12x9.5RM7.6.step",
                    "Buzzer 12 mm", E, el("gpio", None, "2 pins, + marked"),
                    "12 mm through-hole buzzer.", "Give it a small hole in the wall to be heard."),
    "buzzer_piezo": ("sensors", "Buzzer_Beeper.3dshapes/Buzzer_TDK_PS1240P02BT_D12.2mm_H6.5mm.step",
                     "Piezo buzzer 12 mm (TDK PS1240)", E, el("pwm", None, "2 pins, driven with a tone"),
                     "Flat 12 mm piezo sounder.", "Give it a small hole in the wall to be heard."),
    # ----------------------------------------------------------------- relays
    "relay_srd": ("relays", "Relay_THT.3dshapes/Relay_SPDT_SANYOU_SRD_Series_Form_C.step",
                  "Relay SRD (Songle/Sanyou, 10 A)", E,
                  el("gpio", None, "coil + changeover contact (COM, NO, NC)"),
                  "The blue sugar-cube relay of the common relay modules.",
                  "Mains on its contacts needs a closed case and creepage around the pins."),
    "relay_g5le": ("relays", "Relay_THT.3dshapes/Relay_SPDT_Omron-G5LE-1.step",
                   "Relay Omron G5LE", E, el("gpio", None, "coil + changeover contact"),
                   "Omron G5LE 10 A power relay.", ""),
    "relay_g5v1": ("relays", "Relay_THT.3dshapes/Relay_SPDT_Omron_G5V-1.step",
                   "Relay Omron G5V-1 (signal)", E, el("gpio", None, "coil + changeover contact"),
                   "Small signal relay, 1 A.", ""),
    "heatsink_to220": ("relays", "Heatsink.3dshapes/Heatsink_Stonecold_HS-132_32x14mm_2xFixation1.5mm.step",
                       "Heatsink for TO-220 (32 × 14 mm)", "mechanical", None,
                       "Board-mount finned heatsink for a TO-220 part.",
                       "Leave air round the fins; vent the case above it."),
    "heatsink_aavid": ("relays", "Heatsink.3dshapes/Heatsink_AAVID_Extruded_531002B02500G_34.9x12.7mm_H25.4mm.step",
                       "Heatsink AAVID 531002 (25 mm tall)", "mechanical", None,
                       "Extruded board-mount heatsink for TO-220 parts.",
                       "Leave air round the fins; vent the case above it."),
}
CURATED.update(_headers())


# --------------------------------------------------------------- helpers
def _get_json(url):
    import simready
    req = urllib.request.Request(url, headers={"User-Agent": "Prompt2Product"})
    with urllib.request.urlopen(req, timeout=120, context=simready._ssl_context()) as r:
        return json.load(r), r.headers.get("X-Next-Page")


def tree(folder, rev):
    """{path: blob id} of the files in one .3dshapes folder at rev."""
    out, page = {}, "1"
    while page:
        data, page = _get_json(
            "https://gitlab.com/api/v4/projects/%d/repository/tree?ref=%s&path=%s"
            "&per_page=100&page=%s" % (kicad3d.PROJECT_ID, rev, urllib.parse.quote(folder), page))
        for x in data:
            if x["type"] == "blob":
                out[x["path"]] = x["id"]
    return out


def step_author(data):
    """The authors FILE_NAME names in the STEP header, [] when none or blank."""
    head = data[:4000].decode("latin-1", "replace")
    m = re.search(r"FILE_NAME\s*\((.*?)\)\s*;", head, re.S)
    if not m:
        return []
    groups = re.findall(r"\(([^()]*)\)", m.group(1))
    names = re.findall(r"'([^']*)'", groups[0]) if groups else []
    # an e-mail address is left out: the name is the credit, and the release
    # gate (verify_tree's personal-data row) refuses addresses in the bundle
    return [n.strip() for n in names if n.strip() and n.strip().lower() not in
            ("unknown", "author", "") and "@" not in n]


def picture_rel(key):
    return "kicad3d_pictures/%s.png" % key


def write_showcase(groups, path):
    """<key>.bin: uint32 header length, a JSON header {"bbox": [min xyz, max
    xyz] mm, "groups": [{"rgb", "nv", "nt"}]}, padded to 4 bytes, then per
    group nv x 3 uint16 positions (quantised to the bbox, KiCad's Z up) and
    nt x 3 uint32 vertex indices."""
    import struct
    import numpy as np
    allp = np.concatenate([np.asarray(g["points"], dtype=float) for g in groups])
    lo, hi = allp.min(0), allp.max(0)
    span = np.maximum(hi - lo, 1e-9)
    head = {"bbox": [lo.round(4).tolist(), hi.round(4).tolist()],
            "groups": [{"rgb": list(g["rgb"]), "nv": len(g["points"]),
                        "nt": len(g["triangles"])} for g in groups]}
    hj = json.dumps(head).encode()
    hj += b" " * (-(len(hj) + 4) % 4)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<I", len(hj)) + hj)
        for g in groups:
            q = np.round((np.asarray(g["points"]) - lo) / span * 65535).astype("<u2")
            fh.write(q.tobytes())
            if q.size % 2:
                fh.write(b"\0\0")
            fh.write(np.asarray(g["triangles"], dtype="<u4").tobytes())


def colour_pictures(only=None, showcase=None):
    """KICAD_MODE=colour: the pictures redrawn in the models' colours."""
    import numpy as np
    import step_colours
    with open(kicad3d.INDEX, encoding="utf-8") as fh:
        out = json.load(fh)
    tmp = tempfile.mkdtemp(prefix="kicad3d_col_")
    if showcase:
        os.makedirs(showcase, exist_ok=True)
    for key, e in out["parts"].items():
        if only and key not in only:
            continue
        step = kicad3d.fetch(e["path"], e["git_oid"], e["bytes"],
                             os.path.join(tmp, key + ".step"), out["revision"])
        groups, rep = step_colours.coloured_mesh(step, 0.04)
        os.remove(step)
        pts, tris, cols, base = [], [], [], 0
        for g in groups:
            pts += g["points"]
            tris += [(a + base, b + base, c + base) for a, b, c in g["triangles"]]
            cols += [g["rgb"]] * len(g["triangles"])
            base += len(g["points"])
        P = np.asarray(pts)[:, [0, 2, 1]] * np.array([1.0, 1.0, -1.0])   # Z up -> Y up
        render_triangles(P, tris, os.path.join(HERE, picture_rel(key)), cols, cull=False)
        e["colours"] = len(groups)
        if showcase:
            write_showcase(groups, os.path.join(showcase, key + ".bin"))
        print("%-20s %d colours, %d/%d solids matched, %d triangles"
              % (key, len(groups), rep["matched"], rep["solids"], len(tris)))
        sys.stdout.flush()
    with open(kicad3d.INDEX, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def main():
    rev = kicad3d.REVISION
    only = [k for k in os.environ.get("KICAD_ONLY", "").split(",") if k]
    if os.environ.get("KICAD_MODE") == "colour":
        return colour_pictures(only, os.environ.get("KICAD_SHOWCASE"))
    out = {"source": "gitlab.com/" + kicad3d.PROJECT, "revision": rev,
           "licence": kicad3d.LICENCE, "parts": {}}
    if only:
        with open(kicad3d.INDEX, encoding="utf-8") as fh:
            old = json.load(fh)
        out["parts"] = {k: e for k, e in old["parts"].items() if k in CURATED}
    blobs = {}
    for folder in sorted({p.split("/")[0] for _g, p, *_ in CURATED.values()}):
        blobs.update(tree(folder, rev))
    import user_parts
    tmp = tempfile.mkdtemp(prefix="kicad3d_idx_")
    bad = []
    for key, (group, path, shown, cat, elec, desc, notes) in CURATED.items():
        if only and key not in only:
            continue
        assert group in dict(kicad3d.GROUPS), key
        assert cat in user_parts.CATEGORIES, key
        oid = blobs.get(path)
        if oid is None:
            bad.append("%s: %s is not in the library at %s" % (key, path, rev[:12]))
            continue
        step = kicad3d.fetch(path, oid, None, os.path.join(tmp, key + ".step"), rev)
        with open(step, "rb") as fh:
            data = fh.read()
        mesh = user_parts.read_mesh(step)
        if not mesh.CountFacets:
            bad.append("%s: %s meshes to nothing" % (key, path))
            continue
        bb = mesh.BoundBox
        size = [round(bb.XLength, 2), round(bb.YLength, 2), round(bb.ZLength, 2)]
        pic = mesh.copy()
        pic.rotate(-math.pi / 2, 0, 0)            # KiCad's Z-up -> the picture's Y-up
        render_picture(pic, os.path.join(HERE, picture_rel(key)))
        os.remove(step)
        e = {"group": group, "path": path, "git_oid": oid, "bytes": len(data),
             "display_name": shown, "category": cat, "description": desc,
             "agent_notes": notes, "size_mm": size, "triangles": int(mesh.CountFacets),
             "authors": ["KiCad library contributors"] + step_author(data),
             "picture": picture_rel(key)}
        if elec:
            e["electrical"] = elec
        out["parts"][key] = e
        print("%-20s %-10s %s %.0f kB" % (key, group, size, len(data) / 1e3))
        sys.stdout.flush()
    out["parts"] = {k: out["parts"][k] for k in CURATED if k in out["parts"]}
    out["count"] = len(out["parts"])
    with open(kicad3d.INDEX, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    for b in bad:
        print("SKIPPED " + b)
    print("KICAD_INDEX=%d" % len(out["parts"]))


main()
