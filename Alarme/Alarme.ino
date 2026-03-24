const int PIR_PIN = 2; // Broche connectée au signal SIG

void setup() {
  Serial.begin(9600);    // Initialisation de la communication série
  pinMode(PIR_PIN, INPUT);
  Serial.println("Systeme pret. En attente de mouvement...");
}

void loop() {
  int sensorValue = digitalRead(PIR_PIN);

  if (sensorValue == HIGH) {
    // On envoie "1" pour mouvement détecté
    Serial.println("MOTION_DETECTED");
  } else {
    // On envoie "0" pour aucun mouvement
    Serial.println("STILL");
  }
  
  delay(500); // Petite pause pour ne pas saturer le port série
}