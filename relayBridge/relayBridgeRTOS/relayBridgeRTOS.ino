#include <NativeEthernet.h>
#include <aREST.h>
#include <ArduinoJson.h>
#define AREST_PARAMS_MODE 1

const int SERVER_PORT = 8001;

//TODO: How do I want to generate a MAC address?
byte mac[] = {0x00, 0xAA, 0x07, 0x02, 0xFF, 0x52};
//EthernetServer server(80);
EthernetServer server = EthernetServer(SERVER_PORT);
aREST rest = aREST();

byte indexMap[8] = {0, 1, 2, 3, 4, 5, 6, 7};
String arbitrationID = "UnInitialized";

//Where the JSON for the current instruction lives
StaticJsonDocument<200> activeCommand;

//Functions to be exposed to REST API
char* state(String command){
  DeserializationError error = deserializeJson(activeCommand, command);
  if(error){
    return "JSON ERROR";
  }
  byte index = activeCommand["index"];
  if(digitalRead(indexMap[index])) {
    return "true";
  }
  else {
    return "false";
  }
}

char* switchRelay(String command){
  DeserializationError error = deserializeJson(activeCommand, command);
  if(error){
    return 0;
  }
  byte index = activeCommand["index"];
  bool state = activeCommand["state"];
  digitalWrite(indexMap[index], state);
  return "1";
}

char* toggle(String command){
  DeserializationError error = deserializeJson(activeCommand, command);
  if(error){
    return "JSON ERROR";
  }
  byte index = activeCommand["index"];
  if(digitalRead(indexMap[index])) {
    digitalWrite(indexMap[index], LOW);
  }
  else {
    digitalWrite(indexMap[index], HIGH);
  }
  return "1";
}

char* arbitration(String command){
  DeserializationError error = deserializeJson(activeCommand, command);
  if(error){
    return "JSON ERROR";
  }

  Serial.println(rest.method);

  String id = activeCommand['id'];

  if(rest.method == "GET") {
    if(arbitrationID == id) {
      return "True";
    }
    else {
      return "False";
    }
  }
  else if(rest.method == "PUT") {
    arbitrationID = id;
    return "1";
  }
  else{
    return "INVALID COMMAND";
  }
}


void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  ///////////SET ALL PIN MODES/////////////////////
  for (int i = 0; i < sizeof(indexMap); i++) {
    pinMode(indexMap[i], OUTPUT);
  }
  
  //////////ETHERNET STUFF////////////////////////
  Serial.println("Starting ethernet");
  if(not Ethernet.begin(mac)) {
    Serial.println("Ethernet has failed to start");
    if(Ethernet.hardwareStatus() == EthernetNoHardware) {
      Serial.println("No ethernet hardware detected");
    }
    else if(Ethernet.linkStatus() == LinkOFF) {
      Serial.println("Ethernet hardware detected, but nothing is plugged in");
    }
  }
  
  ////////////////REST STUFF//////////////////////////
  rest.function("switch", switchRelay);
  rest.function("state", state);
  rest.function("toggle", toggle);
  rest.function("arbitration", arbitration);
  rest.set_id("008");
  rest.set_name("Relay Bridge");

  server.begin();
  Serial.print("Server started at ");
  Serial.println(Ethernet.localIP());
  Serial.print("Port ");
  Serial.println(SERVER_PORT);
}

void loop() {
  // put your main code here, to run repeatedly:
  EthernetClient client = server.available();
  rest.handle(client);
}
