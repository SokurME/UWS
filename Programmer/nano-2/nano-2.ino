#include <TaskScheduler.h>

//byte cnt = 0; // счетчик для таймера экрана
#define PIN_TRIG 3
#define PIN_ECHO 4

long duration, cm;
unsigned long time;

// Создаем объекты 
Scheduler userScheduler;   // планировщик

void senddata();   //задаем прототип для отправки данных

Task taskSenddata(TASK_MILLISECOND * 500, TASK_FOREVER, &senddata);   //указываем задание

void setup() {
  Serial.begin(9600);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

 //добавляем задания в обработчик
  userScheduler.addTask(taskSenddata);   
  taskSenddata.enable();
}

void loop() {
  //запуск планировщика заданий
  userScheduler.execute();
 // cnt++;
}

void senddata(){
  // Сначала генерируем короткий импульс длительностью 2-5 микросекунд.
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_TRIG, HIGH);
  // Выставив высокий уровень сигнала, ждем около 10 микросекунд. В этот момент датчик будет посылать сигналы с частотой 40 КГц.
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  //  Время задержки акустического сигнала на эхолокаторе.
  duration = pulseIn(PIN_ECHO, HIGH);
  // Теперь осталось преобразовать время в расстояние
  cm = (duration / 2) / 29.1;
 Serial.println(cm);
}