String strData = ""; // для данных с Serial
boolean recievedFlag = false; // флаг получения данных на Serial

void setup(){
Serial.begin(115200);}

void loop(){
	
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
      Serial.print("data from nano...");
      Serial.println(strData);
	  recievedFlag = false;  // данные приняты
     }


	Serial.println("hello from  uno");
	delay(500);
	
	
	
}