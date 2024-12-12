#include <TaskScheduler.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define PIN_BUTTON 4
#define RED 9
#define GRN 10
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
#define pinY    A3  // ось Y джойстика

// Создаем объекты 
Scheduler userScheduler;   // планировщик
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

byte clicks = 0; //количество нажатий кнопки
byte scrCnt = 0; // счетчик для таймера экрана
long recDistance1 = 0; // дистанция 1 с Uno
long recDistance2 = 0; // дистанция 2 с Uno
long diff = 0; // разница
int joystickData = 0; // джойстик

// переменные и константы для обработки сигнала кнопки
boolean flagPress = false;    // признак кнопка в нажатом состоянии
boolean flagClick = false;    // признак нажатия кнопки (фронт)
byte  buttonCount = 0;        // счетчик подтверждений состояния кнопки  
#define TIME_BUTTON 12       // время устойчивого состояния кнопки (* 2 мс) 

boolean flagShowscreen = false;
boolean flagDistance1 = false; // флаг для приема дистанции1
boolean flagDistance2 = false; // флаг для приема дистанции2

String strData = ""; // для данных с Serial
boolean recievedFlag = false; // флаг получения данных на Serial
String tempStr = "";

void showscreen() ;   //задаем прототип для вывода на экран "Start"
void buttonclick();   //задаем прототип для нажатия кнопки
void sendData();   //задаем прототип для отправки данных

Task taskShowscreen(TASK_SECOND * 1 , TASK_FOREVER, &showscreen);   //указываем задание
Task taskButtonclick(TASK_MILLISECOND * 2 , TASK_FOREVER, &buttonclick);   //указываем задание
Task taskSendData(TASK_MILLISECOND * 350 , TASK_FOREVER, &sendData);   //указываем задание

void setup() {
  Serial.begin(9600);

  //инициализация дисплея  
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3D for 128x64

    for(;;); // Don't proceed, loop forever
  }
  // Clear the buffer
  display.clearDisplay();
  display.setTextSize(2);      // Normal 1:1 pixel scale
  display.setTextColor(SSD1306_WHITE); // Draw white text
  display.cp437(true);         // Use full 256 char 'Code Page 437' font

  pinMode(PIN_BUTTON, INPUT_PULLUP); // Устаовили тип пина
  pinMode(RED, OUTPUT);
  pinMode(GRN, OUTPUT);
  pinMode(pinY, INPUT);

  //добавляем задания в обработчик
  userScheduler.addTask(taskShowscreen);   
  userScheduler.addTask(taskButtonclick);
  userScheduler.addTask(taskSendData); 
  taskButtonclick.enable();
  taskSendData.enable();
}

void loop() {
  //запуск планировщика заданий
  userScheduler.execute();
  
 switch (clicks) { 	// проверка порядка нажатия кнопки
 case  1:
  digitalWrite(RED, LOW);
  digitalWrite(GRN, LOW);
  flagDistance2 = false;
  if (!flagShowscreen){
  taskShowscreen.enable();   //включаем задание
  display.clearDisplay();
  display.setTextSize(2);
  display.setCursor(30, 20);     // Start at center
  display.println("Start");
  flagShowscreen = true;
  display.display();
  }
  
  if (scrCnt > 2) {  // через 2 с очищаем дисплей
   taskShowscreen.disable();
   scrCnt = 0;
     if (clicks == 1) {
         display.clearDisplay();
         display.display();
		 }
   }
 break;
 case 2:
 scrCnt = 0;
 if (!flagDistance1){
 display.clearDisplay();
 tempStr = recieveData();
  if (tempStr != "") {
   display.setTextSize(1);
   display.setCursor(0, 0);
   display.print("Distance 1 = ");
   recDistance1 = tempStr.toInt();
   display.println(recDistance1);
   display.display(); 
   flagDistance1 = true;
   }
  }
 tempStr = recieveData(); // читаем, чтобы очищать буфер
 break;
 case 3:
 flagShowscreen = false;
 flagDistance1 = false;
 if (!flagDistance2){
 display.setTextSize(1);
 tempStr = recieveData();
  if (tempStr != "") {
   display.setCursor(0, 20);
   display.print("Distance 2 = ");
   recDistance2 = tempStr.toInt();
   display.println(recDistance2);
   display.setCursor(0, 40);
   display.print("Difference = ");
   diff = recDistance2 - recDistance1; 
   display.println(diff);
   display.display(); 
   flagDistance2 = true;
if ((diff >= 30) && (diff <= 70))
{
    digitalWrite(RED, LOW);
    digitalWrite(GRN, HIGH);
}
if ((diff > 30) && (diff > 70))
{
    digitalWrite(RED, HIGH);
    digitalWrite(GRN, HIGH);
}

if ((diff < 30) && (diff < 70))
{
    digitalWrite(RED, HIGH);
    digitalWrite(GRN, LOW);
}
  }
 }
 tempStr = recieveData(); // читаем, чтобы очищать буфер
 break;
 }
}

void showscreen() {  // отсчет 2 с
 scrCnt++;
}

void buttonclick() { // 
   if (flagPress == (! digitalRead(PIN_BUTTON))) {
     // признак flagPress = текущему состоянию кнопки
     // (инверсия т.к. активное состояние кнопки LOW)
     // т.е. состояние кнопки осталось прежним
     buttonCount = 0;  // сброс счетчика подтверждений состояния кнопки
  }
  else {
     // признак flagPress не = текущему состоянию кнопки
     // состояние кнопки изменилось
     buttonCount++;   // +1 к счетчику состояния кнопки

     if (buttonCount >= TIME_BUTTON) {
      // состояние кнопки не мянялось в течение заданного времени
      // состояние кнопки стало устойчивым
      flagPress = ! flagPress; // инверсия признака состояния
      buttonCount = 0;  // сброс счетчика подтверждений состояния кнопки

      if (flagPress == true) flagClick = true; // признак фронта кнопки на нажатие     
     }   
  }
 
  // блок управления светодиодом
  if (flagClick == true) {
    // было нажатие кнопки
   clicks++;
   if (clicks == 4)
       {clicks = 1;}
 
    flagClick = false;       // сброс признака фронта кнопки


    
  }
}

String recieveData(){
if (Serial.available() > 0) {  // если есть что-то на вход
    strData = "";                // очистить строку
    while (Serial.available() > 0) {
      // пока идут данные
      strData += (char)Serial.read();  // получаем данные
      delay(2);                        // обязательно задержка, иначе вылетим из цикла раньше времени
    }
    recievedFlag = true;  // поднять флаг что получили данные
  }

 if (recievedFlag) {
      recievedFlag = false;  // данные приняты
      return strData;
     }
  else
     return "";

}

void sendData(){
// считать джойстик
joystickData = analogRead(pinY);
Serial.println(joystickData);
}