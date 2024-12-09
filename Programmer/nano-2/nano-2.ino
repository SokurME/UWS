#include <TaskScheduler.h>

byte cnt = 0; // счетчик для таймера экрана

// Создаем объекты 
Scheduler userScheduler;   // планировщик

void senddata();   //задаем прототип для отправки данных

Task taskSenddata(TASK_MILLISECOND * 300, TASK_FOREVER, &senddata);   //указываем задание

void setup() {
  Serial.begin(9600);

 //добавляем задания в обработчик
  userScheduler.addTask(taskSenddata);   
  taskSenddata.enable();
}

void loop() {
  //запуск планировщика заданий
  userScheduler.execute();
  cnt++;
}

void senddata(){
 Serial.println(cnt);
}