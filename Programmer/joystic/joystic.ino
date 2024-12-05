#define pinX    A2  // ось X джойстика
#define pinY    A3  // ось Y джойстика
#define swPin    2  // кнопка джойстика


void setup() {
  Serial.begin(9600);
  

  pinMode(pinX, INPUT);
  pinMode(pinY, INPUT);
  
  pinMode(swPin, INPUT);
  digitalWrite(swPin, HIGH);
}
 
void loop() {
  boolean ledState = digitalRead(swPin); // считываем состояние кнопки


  int X = analogRead(pinX);              // считываем значение оси Х
  int Y = analogRead(pinY);              // считываем значение оси Y

  Serial.print(X);                       // выводим в Serial Monitor
  Serial.print("\t");                    // табуляция
  Serial.println(Y);
}