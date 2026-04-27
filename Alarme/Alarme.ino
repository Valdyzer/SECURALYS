const int PIR_PIN = 2;
const unsigned int ANALYSE_DURATION = 10000; // 10 secondes
const int THRESHOLD = 30; // Seuil de confiance (en %)

// Remplace la logique bloquante par une version non bloquante
enum Mode { IDLE, ANALYZING };
Mode mode = IDLE;
unsigned long analysisStart = 0;
unsigned long lastSampleTime = 0;
unsigned long cooldownStart = 0;
const unsigned long COOLDOWN_MS = 3000;
unsigned int activeCount = 0;
unsigned int totalSamples = 0;

void reportResultAndReset() {
  float activityRatio = (totalSamples == 0) ? 0.0f : (activeCount / (float)totalSamples) * 100.0f;
  Serial.print("Analyse terminee. Activite detectee: ");
  Serial.print(activityRatio);
  Serial.println("%");
  if (activityRatio > THRESHOLD) {
    Serial.println("RESULTAT : PRESENCE CONFIRMEE (Mouvement soutenu)");
    Serial.println("Envoi au logiciel...");
    Serial.println("PRESENCE");
  } else if (activityRatio > 5) {
    Serial.println("RESULTAT : PASSAGE FURTIF (Non significatif)");
    Serial.println("FAUSSE ALERTE");
  } else {
    Serial.println("RESULTAT : BRUIT DE CAPTEUR / SIGNAL FAIBLE");
    Serial.println("FAUSSE ALERTE");
  }
  Serial.println("-------------------------------------------\n");
  cooldownStart = millis();
  mode = IDLE;
}

void setup() {
  Serial.begin(9600);
  pinMode(PIR_PIN, INPUT);
  Serial.println("Systeme d'analyse qualitative pret...");
}


void loop() {
  unsigned long now = millis();
  int sensorValue = digitalRead(PIR_PIN);

  if (mode == IDLE) {
    // Eviter spam serial pendant cooldown
    if (now - cooldownStart >= COOLDOWN_MS) {
      if (sensorValue == HIGH) {
        Serial.println("MOUVEMENT DETECTE");
        mode = ANALYZING;
        analysisStart = now;
        lastSampleTime = 0;
        activeCount = 0;
        totalSamples = 0;
      } else {
        // Affiche moins fréquemment pour éviter spam
        static unsigned long lastCalmePrint = 0;
        if (now - lastCalmePrint >= 2000) {
          Serial.println("CALME");
          lastCalmePrint = now;
        }
      }
    }
  } else { // ANALYZING
    if (lastSampleTime == 0 || now - lastSampleTime >= 100) {
      totalSamples++;
      if (digitalRead(PIR_PIN) == HIGH) activeCount++;
      lastSampleTime = now;
    }
    if (now - analysisStart >= ANALYSE_DURATION) {
      reportResultAndReset();
    }
  }
}


