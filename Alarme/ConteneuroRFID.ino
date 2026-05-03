/**
 * SECURALYS - Conteneur Connecté RFID
 * 
 * Ce code gère :
 * - Lecture des badges ouvriers (entrée/sortie conteneur)
 * - Lecture des tags outils (emprunt/retour)
 * - Mode nuit avec détection PIR
 * - Communication série avec le backend Python
 * 
 * Format des messages série envoyés :
 *   XXXXXXXX             → UID du tag détecté (le backend détermine le type)
 *   ALARME:INTRUSION     → Intrusion détectée en mode nuit
 *   ALARME:OUTIL         → Outil sorti sans badge associé
 *   STATUS:READY         → Système prêt
 *   STATUS:NUIT_ON       → Mode nuit activé
 *   STATUS:NUIT_OFF      → Mode nuit désactivé
 * 
 * Commandes série acceptées :
 *   NUIT:ON              → Activer mode nuit
 *   NUIT:OFF             → Désactiver mode nuit
 *   PING                 → Test connexion (répond PONG)
 * 
 * Matériel requis :
 * - Arduino Mega 2560
 * - Module RFID RC522 (ou compatible)
 * - Capteur PIR pour mode nuit
 * - Buzzer pour alarme
 */

#include <SPI.h>
#include <MFRC522.h>

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION PINS
// ═══════════════════════════════════════════════════════════════════════════

// RFID RC522
#define RST_PIN         9
#define SS_PIN          10  // Arduino Uno : SS matériel = 10 (SDA du RC522)
 
// Capteur PIR (mode nuit)
#define PIR_PIN         2

// Buzzer alarme
#define BUZZER_PIN      8

// LED indicateurs
#define LED_READY       3    // Vert - système prêt
#define LED_BADGE       4    // Bleu - badge détecté
#define LED_OUTIL       5    // Jaune - outil détecté
#define LED_ALARME      6    // Rouge - alarme
#define LED_NUIT        7    // Blanc - mode nuit actif

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION TIMING
// ═══════════════════════════════════════════════════════════════════════════

#define DEBOUNCE_DELAY      2000    // Anti-rebond lecture RFID (ms)
#define ALARM_DURATION      5000    // Durée alarme buzzer (ms)
#define BLINK_INTERVAL      200     // Clignotement LED alarme (ms)

// ═══════════════════════════════════════════════════════════════════════════
// VARIABLES GLOBALES
// ═══════════════════════════════════════════════════════════════════════════

MFRC522 rfid(SS_PIN, RST_PIN);

bool modeNuit = false;
bool alarmeActive = false;
unsigned long lastReadTime = 0;
String lastUID = "";

// ═══════════════════════════════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════════════════════════════

void setup() {
    // Communication série
    Serial.begin(9600);
    // Ne pas bloquer sur Serial pour une Uno
    
    // Initialisation SPI et RFID
    SPI.begin();
    // Sur Arduino, s'assurer que la broche SS est en OUTPUT pour rester maître SPI
    pinMode(SS_PIN, OUTPUT);
    rfid.PCD_Init();
    
    // Configuration des pins
    pinMode(PIR_PIN, INPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(LED_READY, OUTPUT);
    pinMode(LED_BADGE, OUTPUT);
    pinMode(LED_OUTIL, OUTPUT);
    pinMode(LED_ALARME, OUTPUT);
    pinMode(LED_NUIT, OUTPUT);
    
    // État initial
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_READY, HIGH);
    digitalWrite(LED_BADGE, LOW);
    digitalWrite(LED_OUTIL, LOW);
    digitalWrite(LED_ALARME, LOW);
    digitalWrite(LED_NUIT, LOW);
    
    Serial.println("STATUS:READY");
}

// ═══════════════════════════════════════════════════════════════════════════
// LOOP PRINCIPALE
// ═══════════════════════════════════════════════════════════════════════════

void loop() {
    // Traiter les commandes série entrantes
    handleSerialCommands();
    
    // Mode nuit : surveiller PIR
    if (modeNuit) {
        checkPIR();
    }
    
    // Lecture RFID (si pas d'alarme active)
    if (!alarmeActive) {
        checkRFID();
    }
    
    delay(50);
}

// ═══════════════════════════════════════════════════════════════════════════
// GESTION COMMANDES SÉRIE
// ═══════════════════════════════════════════════════════════════════════════

void handleSerialCommands() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command == "PING") {
            Serial.println("PONG");
        }
        else if (command == "NUIT:ON") {
            modeNuit = true;
            digitalWrite(LED_NUIT, HIGH);
            Serial.println("STATUS:NUIT_ON");
        }
        else if (command == "NUIT:OFF") {
            modeNuit = false;
            digitalWrite(LED_NUIT, LOW);
            alarmeActive = false;
            digitalWrite(BUZZER_PIN, LOW);
            digitalWrite(LED_ALARME, LOW);
            Serial.println("STATUS:NUIT_OFF");
        }
        else if (command == "ALARM:STOP") {
            stopAlarm();
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// LECTURE RFID
// ═══════════════════════════════════════════════════════════════════════════

void checkRFID() {
    // Vérifier si une nouvelle carte est présente
    if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
        return;
    }
    
    // Lire l'UID
    String uid = getUID();
    
    // Anti-rebond : ignorer si même carte lue récemment
    unsigned long currentTime = millis();
    if (uid == lastUID && (currentTime - lastReadTime) < DEBOUNCE_DELAY) {
        rfid.PICC_HaltA();
        rfid.PCD_StopCrypto1();
        return;
    }
    
    lastUID = uid;
    lastReadTime = currentTime;
    
    Serial.println(uid);
    /*
    // Déterminer le type de tag (badge ou outil)
    // Convention : les badges commencent par "B", les outils par "O"
    // ou on peut distinguer par la longueur/format
    String tagType = determineTagType(uid);


    if (tagType == "BADGE") {
        digitalWrite(LED_BADGE, HIGH);
        Serial.println("BADGE:" + uid);
        delay(500);
        digitalWrite(LED_BADGE, LOW);
    }
    else if (tagType == "OUTIL") {
        digitalWrite(LED_OUTIL, HIGH);
        Serial.println("OUTIL:" + uid);
        delay(500);
        digitalWrite(LED_OUTIL, LOW);
    }
    */
    // Arrêter la communication avec la carte
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
}

String getUID() {
    String uid = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) {
            uid += "0";
        }
        uid += String(rfid.uid.uidByte[i], HEX);
    }
    uid.toUpperCase();
    return uid;
}

/*
String determineTagType(String uid) {
    // Pour ce prototype, on utilise une convention simple :
    // - Les 4 premiers caractères déterminent le type
    // - En production, cela serait configuré dans une EEPROM
    //   ou déterminé par le backend qui connaît tous les tags
    
    // Option 1 : Préfixe dans l'UID (si tags programmables)
    // Option 2 : Le backend détermine le type
    
    // Pour l'instant, on envoie tous les tags comme "OUTIL"
    // et le badge comme "BADGE" si le premier octet est pair
    // (simplification pour le prototype)
    
    if (rfid.uid.uidByte[0] % 2 == 0) {
        return "BADGE";
    }
    return "OUTIL";
}
*/

// ═══════════════════════════════════════════════════════════════════════════
// MODE NUIT - DÉTECTION PIR
// ═══════════════════════════════════════════════════════════════════════════

void checkPIR() {
    if (digitalRead(PIR_PIN) == HIGH && !alarmeActive) {
        // Mouvement détecté en mode nuit = intrusion !
        triggerAlarm("INTRUSION");
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// GESTION ALARME
// ═══════════════════════════════════════════════════════════════════════════

void triggerAlarm(String reason) {
    alarmeActive = true;
    Serial.println("ALARME:" + reason);
    
    // Alarme sonore et visuelle
    unsigned long startTime = millis();
    while (millis() - startTime < ALARM_DURATION && alarmeActive) {
        digitalWrite(BUZZER_PIN, HIGH);
        digitalWrite(LED_ALARME, HIGH);
        delay(BLINK_INTERVAL);
        digitalWrite(BUZZER_PIN, LOW);
        digitalWrite(LED_ALARME, LOW);
        delay(BLINK_INTERVAL);
        
        // Vérifier si commande d'arrêt reçue
        handleSerialCommands();
    }
    
    stopAlarm();
}

void stopAlarm() {
    alarmeActive = false;
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_ALARME, LOW);
}
