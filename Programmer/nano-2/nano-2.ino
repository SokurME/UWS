#include <TaskScheduler.h>

//byte cnt = 0; // счетчик для таймера экрана
#define trigPin 3
#define echoPin 4

int counter;
float duration;
float distance;
unsigned long time;

// Создаем объекты 
Scheduler userScheduler;   // планировщик

void senddata();   //задаем прототип для отправки данных

Task taskSenddata(TASK_MILLISECOND * 1000, TASK_FOREVER, &senddata);   //указываем задание

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

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
  digitalWrite(trigPin, LOW); 
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite( trigPin, LOW );
  
//  duration = pulseIn( echoPin, HIGH ); 

  // Get Pulse duration with more accuracy than pulseIn()
  duration = 0;
  counter = 0;
  while(--counter!=0 )
  {
    	if( PINB & 2 ) 
    	{
    	  time = micros();
    	  break;
    	}
  }
  counter = 0;
  while( --counter!=0 )
  {
    	if( (PINB & 2)==0 ) 
    	{
    	  duration = micros()-time;
    	  break;
    	}
  }

  distance = ( duration/2 ) * 0.0344;
  
 /* Serial.print("Distance: ");

  if     ( distance > 400 ) Serial.print("> 400");
  else if( distance < 2 )   Serial.print("< 2");
  else                      Serial.print( distance );

  Serial.println( " cm" );*/
 Serial.println(distance);
}