# 1.54"-st7789-eye-display.py
# Using a 1.54" 240x240 Wide Angle TFT LCD Display with ST7789 controller
# with EyeSPI Connector. Wired to a Raspberry Pi Pico (works with all picos, incl. 2s & Ws)
# Adapted from @TodBot's cool demo and modified for ST7789 display
# Update pins for your board & be sure you have the imgs folder with eyeball images
# on your CIRCUITPY board

import board, displayio, terminalio, busio, time, adafruit_imageload, math, random, digitalio
from adafruit_st7789 import ST7789

# Release any existing displays
displayio.release_displays()

# Setup backlight control (optional - comment out if you don't want backlight control)
backlight = digitalio.DigitalInOut(board.GP2)
backlight.direction = digitalio.Direction.OUTPUT
backlight.value = True  # Turn on backlight

# wiring for Raspberry Pi Pico with EyeSPI connector
tft0_clk  = board.GP18  # SCK
tft0_mosi = board.GP19  # MOSI (Data Out)
tft_L0_dc  = board.GP21  # DC (Data/Command)
tft_L0_cs  = board.GP17  # TCS (Chip Select) - Updated from GP20 to GP17
tft_L0_rst = board.GP15  # RST (Reset)
spi0 = busio.SPI(clock=tft0_clk, MOSI=tft0_mosi)

# Set the display's dimensions
dw, dh = 240,240  # display dimensions
rot = 0

# load our eye and iris bitmaps
eyeball_bitmap, eyeball_pal = adafruit_imageload.load("imgs/eye0_ball2.bmp")
iris_bitmap, iris_pal = adafruit_imageload.load("imgs/eye0_iris0.bmp")
# eyeball_bitmap, eyeball_pal = adafruit_imageload.load("imgs/Lizard_Sclera.bmp")
# iris_bitmap, iris_pal = adafruit_imageload.load("imgs/Lizard_Iris_White.bmp")
iris_pal.make_transparent(0)  # palette color #0 is our transparent background

# compute or declare some useful info about the eyes
iris_w, iris_h = iris_bitmap.width, iris_bitmap.height  # iris is normally 110x110
iris_cx, iris_cy = dw//2 - iris_w//2, dh//2 - iris_h//2 # center point of iris
r = 30  # allowable deviation from center for iris

# class to help us track eye info (not needed for this use exactly, but I find it interesting)
class Eye:
    # Below is the initializtion or setup class
    def __init__(self, spi, dc, cs, rst, rot=90, eye_speed=0.25, twitch=2):
        # Create the display bus & use this to create a display from the ST7789 display type
        # ST7789 is the display controller chip from Sitronix Technology Corp.
        # This chip handles low level essentials for the display.
        # The ST7789 class interfaces between a display w/this chip & CircuitPython.
        display_bus = displayio.FourWire(spi, command=dc, chip_select=cs, reset=rst)
        display = ST7789(display_bus, width=dw, height=dh, rotation=rot, rowstart=80, colstart=0)

        # Setup the eye & eyeball images
        main = displayio.Group()
        display.root_group = main # You always create a group & add it to the display
        self.display = display
        self.eyeball = displayio.TileGrid(eyeball_bitmap, pixel_shader=eyeball_pal) # This is a rectangle containing our eyeball image
        self.iris = displayio.TileGrid(iris_bitmap, pixel_shader=iris_pal, x=iris_cx,y=iris_cy) # and another one with our iris image
        main.append(self.eyeball) # Add these images to the display
        main.append(self.iris)
        self.x, self.y = iris_cx, iris_cy # current iris position (not "eye position")
        self.tx, self.ty = self.x, self.y # target iris position. Both start in center.
        self.next_time = time.monotonic()
        self.eye_speed = eye_speed
        self.twitch = twitch # Maximum time (seconds) before movement to a new target point

    def update(self):
        # This code will smoothly move the eye instead of an instant jump
        # Keep 75% of current position + 25% of target position
        # Each frame, the iris moves 1/4 of the way closer to the target
        # it never mathematically "reaches" the target, but may seem to given the int conversion
        self.x = self.x * (1-self.eye_speed) + self.tx * self.eye_speed # "easing"
        self.y = self.y * (1-self.eye_speed) + self.ty * self.eye_speed
        self.iris.x = int( self.x ) # Move iris Tile toward the target using value calculated above
        self.iris.y = int( self.y )
        if time.monotonic() > self.next_time: # is it time for a new target?
            t = random.uniform(0.25,self.twitch) # Random time until next target is chosen
            self.next_time = time.monotonic() + t # Schedule the next target change
            self.tx = iris_cx + random.uniform(-r,r) # New random X target (within radius r)
            self.ty = iris_cy + random.uniform(-r,r) # New random Y target (within radius r)
        self.display.refresh() # updates the display to show Tile movement for iris

# a list of all the eyes, in this case, only one
# You can create more eyes if you'd like, they would each move independently.
# If you wanted eyes to move together, you'd have to create and share a single
# target and twitch time and modify code to share between all eyes.
the_eyes = [
    Eye( spi0, tft_L0_dc, tft_L0_cs,  tft_L0_rst, rot=90),
]

print("Display Running!")
while True:
    for eye in the_eyes: # Go through all eyes
        eye.update() # Move eye either toward target location and perhaps choose a new target

