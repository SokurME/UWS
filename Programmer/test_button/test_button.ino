#include <TaskScheduler.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define PIN_BUTTON 4
#define PIN_LED 9
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)

// Создаем объекты 
Scheduler userScheduler;   // планировщик
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

int start_text[] = { 83, 84, 65, 82, 84   };
int distance1[] = { 68, 73, 83, 84, 65, 78, 67, 69, 49, 58   };
int distance2[] = { 68, 73, 83, 84, 65, 78, 67, 69, 50, 58   };
int depth[] = { 68, 69, 80, 84, 72, 58  };
int clicks = 0; //количество нажатий кнопки
boolean ledState = false;            // переменная состояния светодиода 
byte scrCnt = 0; // счетчик для таймера экрана

// переменные и константы для обработки сигнала кнопки
boolean flagPress = false;    // признак кнопка в нажатом состоянии
boolean flagClick = false;    // признак нажатия кнопки (фронт)
byte  buttonCount = 0;        // счетчик подтверждений состояния кнопки  
#define TIME_BUTTON 12       // время устойчивого состояния кнопки (* 2 мс) 

boolean flagShowscreen = false;

void showscreen() ;   //задаем прототип для вывода на экран "Start"
void buttonclick();   //задаем прототип для нажатия кнопки

Task taskShowscreen(TASK_SECOND * 1 , TASK_FOREVER, &showscreen);   //указываем задание
Task taskButtonclick(TASK_MILLISECOND * 2 , TASK_FOREVER, &buttonclick);   //указываем задание
void setup() {
  Serial.begin(115200);

  //инициализация дисплея  
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3D for 128x64
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
  // Clear the buffer
  display.clearDisplay();

  pinMode(PIN_BUTTON, INPUT_PULLUP); // Устаовили тип пина
  pinMode(PIN_LED, OUTPUT);  //Setup the LED

  //добавляем задания в обработчик
  userScheduler.addTask(taskShowscreen);   
  userScheduler.addTask(taskButtonclick);   
  taskButtonclick.enable();
}

void loop() {
  //запуск планировщика заданий
  userScheduler.execute();
  
 switch (clicks) {
 case  1:
  if (!flagShowscreen){
  taskShowscreen.enable();   //включаем задание
  display.clearDisplay();
  display.setTextSize(1);      // Normal 1:1 pixel scale
  display.setTextColor(SSD1306_WHITE); // Draw white text
  display.setCursor(0, 0);     // Start at top-left corner
  display.cp437(true);         // Use full 256 char 'Code Page 437' font
  for (int i = 0; i < 5; i++) {
    display.write(start_text[i]);
  }
  flagShowscreen = true;}
  display.display();
  if (scrCnt > 2) {  // через 2 с очищаем дисплей
   taskShowscreen.disable();
   scrCnt = 0;
   if (clicks == 1) display.clearDisplay();
}
 break;
 case 2:
 break;
 case 3:
   flagShowscreen = false;
 break;
 }
}

void showscreen() {
 scrCnt++;
}

void buttonclick() {
   if (flagPress == (! digitalRead(PIN_BUTTON))) {
     // признак flagPress = текущему состоянию кнопки
     // (инверсия т.к. активное состояние кнопки LOW)
     // т.е. состояние кнопки осталось прежним
     buttonCount= 0;  // сброс счетчика подтверждений состояния кнопки
  }
  else {
     // признак flagPress не = текущему состоянию кнопки
     // состояние кнопки изменилось
     buttonCount++;   // +1 к счетчику состояния кнопки

     if (buttonCount >= TIME_BUTTON) {
      // состояние кнопки не мянялось в течение заданного времени
      // состояние кнопки стало устойчивым
      flagPress= ! flagPress; // инверсия признака состояния
      buttonCount= 0;  // сброс счетчика подтверждений состояния кнопки

      if (flagPress == true) flagClick= true; // признак фронта кнопки на нажатие     
     }   
  }
 
  // блок управления светодиодом
  if (flagClick == true) {
    // было нажатие кнопки
  clicks++;
  Serial.println(clicks);
    flagClick= false;       // сброс признака фронта кнопки
    ledState= ! ledState;   // инверсия состояние светодиода
    digitalWrite(PIN_LED, ledState);  // вывод состояния светодиода   
    if (clicks == 3){clicks = 0;}
  }
}