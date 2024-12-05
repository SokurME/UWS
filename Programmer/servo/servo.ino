
#include <Servo.h>

Servo myservo;
int start_position;
int end_position =180;
int step = 1;
void setup() 
{
  myservo.attach( 9, 1000, 2000 );
  pinMode( 13, OUTPUT );
Serial.begin(9600);
}

void loop() {
start_position = myservo.read();
Serial.println(start_position);
int pos;
if(end_position > start_position){
  for( pos=start_position; pos<=end_position; pos += step)
  {
    delay( 100 );
    
    myservo.write( pos );
    
    delay( 10 );
  }}
else{
  for( pos=start_position; pos>=end_position; pos -= step)
  {
    delay( 100 );
    
    myservo.write( pos );
    
    delay( 10 );
  }}
  delay( 100 );

}