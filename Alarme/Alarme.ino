const int PIR_PIN = 2;
const unsigned int ANALYSE_DURATION = 10000; // 10 secondes
const int THRESHOLD = 30; // Seuil de confiance (en %)


void analyzeMovement() {
  Serial.println(">>> Debut de l'analyse qualitative (10s)...");
  
  unsigned long startTime = millis();
  unsigned int activeCount = 0;
  unsigned int totalSamples = 0;

  // Boucle d'analyse active pendant 10 secondes
  while (millis() - startTime < ANALYSE_DURATION) {
    totalSamples++;
    if (digitalRead(PIR_PIN) == HIGH) {
      activeCount++;
    }
    delay(100); // Echantillonnage tous les 1/10eme de seconde
  }

  // Calcul du ratio d'activité en pourcentage
  float activityRatio = (activeCount / (float)totalSamples) * 100;

  Serial.print("Analyse terminee. Activite detectee: ");
  Serial.print(activityRatio);
  Serial.println("%");

  if (activityRatio > THRESHOLD) {
    Serial.println("RESULTAT : PRESENCE CONFIRMEE (Mouvement soutenu)");
    Serial.println("Envoi au logiciel...");
    Serial.println("PRESENCE");
    delay(3000);

  } else if (activityRatio > 5) {
    Serial.println("RESULTAT : PASSAGE FURTIF (Non significatif)");
    Serial.println("FAUSSE ALERTE");
    delay(3000);

  } else {
    Serial.println("RESULTAT : BRUIT DE CAPTEUR / SIGNAL FAIBLE");
    Serial.println("FAUSSE ALERTE");
    delay(3000);
  }
  
  Serial.println("-------------------------------------------\n");
}


void setup() {
  Serial.begin(9600);
  pinMode(PIR_PIN, INPUT);
  Serial.println("Systeme d'analyse qualitative pret...");
}


void loop() {
  int sensorValue = digitalRead(PIR_PIN);

  if (sensorValue == HIGH) {
    Serial.println("MOUVEMENT DETECTE");
    analyzeMovement();
  }
  else if (sensorValue == LOW) {
    Serial.println("CALME");
  }

  delay(500); 
}


