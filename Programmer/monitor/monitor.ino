//48, 49, 50, 51, 52, 53, 54, 55, 56, 57
//0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

int start_text[] =
{ 83, 84, 65, 82, 84   };

int distance1[] =
{ 68, 73, 83, 84, 65, 78, 67, 69, 49, 58   };

int distance2[] =
{ 68, 73, 83, 84, 65, 78, 67, 69, 50, 58   };

int depth[] =
{ 68, 69, 80, 84, 72, 58  };

void setup() {
  Serial.begin(9600);

  // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3D for 128x64
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
  // Show initial display buffer contents on the screen --
  // the library initializes this with an Adafruit splash screen.
 // display.display();
  //delay(2000); // Pause for 2 seconds

  // Clear the buffer
  display.clearDisplay();
 beginning_began();      // Draw characters of the default font
 pin_out();
}

void loop() {
}


void beginning_began(void) {
int i;
  display.clearDisplay();

  display.setTextSize(1);      // Normal 1:1 pixel scale
  display.setTextColor(SSD1306_WHITE); // Draw white text
  display.setCursor(0, 0);     // Start at top-left corner
  display.cp437(true);         // Use full 256 char 'Code Page 437' font

  // Not all the characters will fit on the display. This is normal.
  // Library will draw what it can and the rest will be clipped.

 for (i = 0; i < 5
; i++) {
display.write(start_text[i]);
}
 
  display.display();
  delay(2000);
}


void pin_out(void) {
int i;
  display.clearDisplay();

  display.setTextSize(1);      // Normal 1:1 pixel scale
  display.setTextColor(SSD1306_WHITE); // Draw white text
  display.setCursor(0, 0);     // Start at top-left corner
  display.cp437(true);         // Use full 256 char 'Code Page 437' font

  // Not all the characters will fit on the display. This is normal.
  // Library will draw what it can and the rest will be clipped.

for (i = 0; i < 10; i++) {
display.write(distance1[i]);
}

display.setCursor(0, 10);

for (i = 0; i < 10; i++) {
display.write(distance2[i]);
}

display.setCursor(0, 20);

for (i = 0; i < 6; i++) {
display.write(depth[i]);
}

  display.display();
  delay(2000);
}