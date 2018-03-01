/*
 * First LED ring is UI indicator then bottles.
 * Bottle numbers are 0-indexed.
 */

#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
  #include <avr/power.h>
#endif

#define NUM_BOTTLES 8
#define NEO_PIN 6
#define BASE_BRIGHTNESS 50
#define RAISED_BRIGHTNESS 200
#define MAX_CMD_SIZE 8

// Parameter 1 = number of pixels in strip
// Parameter 2 = Arduino pin number (most are valid)
// Parameter 3 = pixel type flags, add together as needed:
//   NEO_KHZ800  800 KHz bitstream (most NeoPixel products w/WS2812 LEDs)
//   NEO_KHZ400  400 KHz (classic 'v1' (not v2) FLORA pixels, WS2811 drivers)
//   NEO_GRB     Pixels are wired for GRB bitstream (most NeoPixel products)
//   NEO_RGB     Pixels are wired for RGB bitstream (v1 FLORA pixels, not v2)
//   NEO_RGBW    Pixels are wired for RGBW bitstream (NeoPixel RGBW products)
Adafruit_NeoPixel strip = Adafruit_NeoPixel(216, NEO_PIN, NEO_GRB + NEO_KHZ800);

// IMPORTANT: To reduce NeoPixel burnout risk, add 1000 uF capacitor across
// pixel power leads, add 300 - 500 Ohm resistor on first pixel's data input
// and minimize distance between Arduino and first pixel.  Avoid connecting
// on a live circuit...if you must, connect GND first.

/*
 * Array to hold incoming serial commands
 */
char cmd[MAX_CMD_SIZE];
uint16_t index = 0;

/*
 * conversational ux
 * o = off
 * h = hotword
 * l = listening
 * t = thinking
 * r = responding
 */
char _cuxState = 'o';
int16_t _iterNum = 0;
uint8_t _cuxUp = 1;

/*
 * bottle ux
 * o = off
 * r = responding
 */
 
char _b0uxState = 'o';
int16_t _b0iterNum = 0;
uint8_t _b0uxUp = 1;

char _b1uxState = 'o';
int16_t _b1iterNum = 0;
uint8_t _b1uxUp = 1;

char _b2uxState = 'o';
int16_t _b2iterNum = 0;
uint8_t _b2uxUp = 1;

char _b3uxState = 'o';
int16_t _b3iterNum = 0;
uint8_t _b3uxUp = 1;

char _b4uxState = 'o';
int16_t _b4iterNum = 0;
uint8_t _b4uxUp = 1;

char _b5uxState = 'o';
int16_t _b5iterNum = 0;
uint8_t _b5uxUp = 1;

char _b6uxState = 'o';
int16_t _b6iterNum = 0;
uint8_t _b6uxUp = 1;

char _b7uxState = 'o';
int16_t _b7iterNum = 0;
uint8_t _b7uxUp = 1;

// in order of bottles
uint8_t _relayPins[] = { 2, 3, 4, 5, 7, 8, 9, 10 };

void setup() {

  // start serial
  Serial.begin(9600);

  // set pin modes for relays
  for (uint8_t i = 0; i < NUM_BOTTLES; i++) {
    pinMode(_relayPins[i], OUTPUT);
  }

  // start neopixel strip and turn pixels off
  strip.begin();
  allOff();
}

void loop() {

  // check for available serial data
  if (Serial.available() > 0) {

    // append char to command
    cmd[index] = Serial.read();

    // if character is NOT command terminator
    if (cmd[index] != '!') {

      // increment command index
      index++;
    }

    // else process entire command
    else {

      // was command valid? default to yes
      uint8_t cmdValid = 1;
      char cmd0 = cmd[0];
      char cmd1 = cmd[1];
      char cmd2 = cmd[2];

      // bottle commands
      if (cmd0 == 'b') {

        // parse command
        char temp[2] = { cmd1, '\0' };
        uint8_t bottleNum = atoi(temp);

        // change state based on action
        switch (cmd2) {
          case 'r':
            // turn on relay
            digitalWrite(_relayPins[bottleNum], HIGH);
            cmd0 = cmd1;
            cmd1 = 'r';
            break;
          case 'l':
            // turn off relay
            digitalWrite(_relayPins[bottleNum], LOW);
            cmd0 = cmd1;
            cmd1 = 'o';
            break;
          default:
            cmdValid = 0;
            break;
        }
      }

      // ui commands
      if  (cmd0 == 'x') {
        // todo: check for valid cmd[1]
        _cuxState = cmd1;
        _iterNum = 0;
      }
      else if  (cmd0 == '0') {
        _b0uxState = cmd1;
        _b0iterNum = 0;
      }
      else if  (cmd0 == '1') {
        _b1uxState = cmd1;
        _b1iterNum = 0;
      }
      else if  (cmd0 == '2') {
        _b2uxState = cmd1;
        _b2iterNum = 0;
      }
      else if  (cmd0 == '3') {
        _b3uxState = cmd1;
        _b3iterNum = 0;
      }
      else if  (cmd0 == '4') {
        _b4uxState = cmd1;
        _b4iterNum = 0;
      }
      else if  (cmd0 == '5') {
        _b5uxState = cmd1;
        _b5iterNum = 0;
      }
      else if  (cmd0 == '6') {
        _b6uxState = cmd1;
        _b6iterNum = 0;
      }
      else if  (cmd0 == '7') {
        _b7uxState = cmd1;
        _b7iterNum = 0;
      }

      // bad command
      else {
        cmdValid = 0;
      }

      // send response
      if (cmdValid == 1) {
        Serial.println("OK");
      } else if (cmdValid == 0) {
        Serial.println("ERR");
      } else {
        Serial.println("?");
      }

      // reset the command buffer and index
      resetCmd();
    }
  }

  // do conversational ux state
  switch (_cuxState) {
    case 'o':
      _iterNum += cuxOff(_iterNum);
      break;
    case 'h':
      _iterNum += cuxHotword(_iterNum);
      break;
    case 'l':
      _iterNum += cuxListening(_iterNum);
      break;
    case 't':
      _iterNum += cuxThinking(_iterNum);
      break;
    case 'r':
      _iterNum += cuxResponding(_iterNum);
      break;
  }

  // do b0 state
  switch (_b0uxState) {
    case 'o':
      _b0iterNum += b0uxOff(_b0iterNum);
      break;
    case 'r':
      _b0iterNum += b0uxResponding(_b0iterNum);
      break;
  }

  // do b1 state
  switch (_b1uxState) {
    case 'o':
      _b1iterNum += b1uxOff(_b1iterNum);
      break;
    case 'r':
      _b1iterNum += b1uxResponding(_b1iterNum);
      break;
  }

  // do b2 state
  switch (_b2uxState) {
    case 'o':
      _b2iterNum += b2uxOff(_b2iterNum);
      break;
    case 'r':
      _b2iterNum += b2uxResponding(_b2iterNum);
      break;
  }

  // do b3 state
  switch (_b3uxState) {
    case 'o':
      _b3iterNum += b3uxOff(_b3iterNum);
      break;
    case 'r':
      _b3iterNum += b3uxResponding(_b3iterNum);
      break;
  }

  // do b4 state
  switch (_b4uxState) {
    case 'o':
      _b4iterNum += b4uxOff(_b4iterNum);
      break;
    case 'r':
      _b4iterNum += b4uxResponding(_b4iterNum);
      break;
  }

  // do b5 state
  switch (_b5uxState) {
    case 'o':
      _b5iterNum += b5uxOff(_b5iterNum);
      break;
    case 'r':
      _b5iterNum += b5uxResponding(_b5iterNum);
      break;
  }

  // do b6 state
  switch (_b6uxState) {
    case 'o':
      _b6iterNum += b6uxOff(_b6iterNum);
      break;
    case 'r':
      _b6iterNum += b6uxResponding(_b6iterNum);
      break;
  }

  // do b7 state
  switch (_b7uxState) {
    case 'o':
      _b7iterNum += b7uxOff(_b7iterNum);
      break;
    case 'r':
      _b7iterNum += b7uxResponding(_b7iterNum);
      break;
  }
  
  delay(10);
}

/*
 * Conversational UX off
 */
int16_t cuxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 0; px < 24; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}

/*
 * b0 UX off
 */
int16_t b0uxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 24; px < 48; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}

/*
 * b1 UX off
 */
int16_t b1uxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 48; px < 72; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}

/*
 * b2 UX off
 */
int16_t b2uxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 72; px < 96; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}

/*
 * b3 UX off
 */
int16_t b3uxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 96; px < 120; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}


/*
 * b4 UX off
 */
int16_t b4uxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 120; px < 144; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}


/*
 * b5 UX off
 */
int16_t b5uxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 144; px < 168; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}

/*
 * b6 UX off
 */
int16_t b6uxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 168; px < 192; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}

/*
 * b7 UX off
 */
int16_t b7uxOff(int16_t iterNum) {

  // done
  if (iterNum > 0) {
    return 0;
  }

  // turn all pixels off
  for (uint8_t px = 192; px < 216; px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();

  return 1;
}

/*
 * Conversational UX hotword
 */
int16_t cuxHotword(int16_t iterNum) {

  // animation is finished
  if (iterNum > 23) {

    // todo: is this hacky?
    _cuxState = 'l';
    _iterNum = 0;

    return 0;
  }

  // clear pixels on first iteration
  if (iterNum == 0) {
    for (uint8_t px = 0; px < 24; px++) {
      strip.setPixelColor(px, 0, 0, 0);
    }
  }

  // set proper pixel color
  strip.setPixelColor(iterNum, BASE_BRIGHTNESS, BASE_BRIGHTNESS, BASE_BRIGHTNESS);
  strip.show();

  // additional delay for timing
  delay(25);

  return 1;
}

/*
 * Conversational UX listening
 */
int16_t cuxListening(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 0; px < 24; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _cuxUp = 0;
  } else if (iterNum <= 0) {
    _cuxUp = 1;
  }

  // return value based on direction
  if (_cuxUp == 1) {
    return 1;
  } else if (_cuxUp == 0) {
    return -1;
  }
  return 0;
}

/*
 * Conversational UX thinking
 */
int16_t cuxThinking(int16_t iterNum) {

  // turn all pixels off on first iteration
  if (iterNum == 0) {
    for (uint8_t px = 0; px < 24; px++) {
      strip.setPixelColor(px, 0, 0, 0);
    }
  }

  // calculate current and last pixels
  int8_t currentPixel = iterNum % 24;
  int8_t lastPixel = currentPixel - 1;
  if (lastPixel == -1) {
    lastPixel = 23;
  }

  // turn last pixel off and current pixel on
  strip.setPixelColor(lastPixel, 0, 0, 0);
  strip.setPixelColor(currentPixel, BASE_BRIGHTNESS, BASE_BRIGHTNESS, BASE_BRIGHTNESS);
  strip.show();

  // additional delay for timing
  delay(100);

  // return value
  if (iterNum == 23) {
    return -23;
  }
  return 1;
}

/*
 * Conversational UX responding
 */
int16_t cuxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 0; px < 24; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _cuxUp = 0;
  } else if (iterNum <= 0) {
    _cuxUp = 1;
  }

  // return value based on direction
  if (_cuxUp == 1) {
    return 2;
  } else if (_cuxUp == 0) {
    return -2;
  }
  return 0;
}

/*
 * b0 UX responding
 */
int16_t b0uxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 24; px < 48; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _b0uxUp = 0;
  } else if (iterNum <= 0) {
    _b0uxUp = 1;
  }

  // return value based on direction
  if (_b0uxUp == 1) {
    return 2;
  } else if (_b0uxUp == 0) {
    return -2;
  }
  return 0;
}

/*
 * b1 UX responding
 */
int16_t b1uxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 48; px < 72; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _b1uxUp = 0;
  } else if (iterNum <= 0) {
    _b1uxUp = 1;
  }

  // return value based on direction
  if (_b1uxUp == 1) {
    return 2;
  } else if (_b1uxUp == 0) {
    return -2;
  }
  return 0;
}

/*
 * b2 UX responding
 */
int16_t b2uxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 72; px < 96; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _b2uxUp = 0;
  } else if (iterNum <= 0) {
    _b2uxUp = 1;
  }

  // return value based on direction
  if (_b2uxUp == 1) {
    return 2;
  } else if (_b2uxUp == 0) {
    return -2;
  }
  return 0;
}

/*
 * b3 UX responding
 */
int16_t b3uxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 96; px < 120; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _b3uxUp = 0;
  } else if (iterNum <= 0) {
    _b3uxUp = 1;
  }

  // return value based on direction
  if (_b3uxUp == 1) {
    return 2;
  } else if (_b3uxUp == 0) {
    return -2;
  }
  return 0;
}

/*
 * b4 UX responding
 */
int16_t b4uxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 120; px < 144; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _b4uxUp = 0;
  } else if (iterNum <= 0) {
    _b4uxUp = 1;
  }

  // return value based on direction
  if (_b4uxUp == 1) {
    return 2;
  } else if (_b4uxUp == 0) {
    return -2;
  }
  return 0;
}

/*
 * b5 UX responding
 */
int16_t b5uxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 144; px < 168; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _b5uxUp = 0;
  } else if (iterNum <= 0) {
    _b5uxUp = 1;
  }

  // return value based on direction
  if (_b5uxUp == 1) {
    return 2;
  } else if (_b5uxUp == 0) {
    return -2;
  }
  return 0;
}

/*
 * b6 UX responding
 */
int16_t b6uxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 168; px < 192; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _b6uxUp = 0;
  } else if (iterNum <= 0) {
    _b6uxUp = 1;
  }

  // return value based on direction
  if (_b6uxUp == 1) {
    return 2;
  } else if (_b6uxUp == 0) {
    return -2;
  }
  return 0;
}

/*
 * b7 UX responding
 */
int16_t b7uxResponding(int16_t iterNum) {

  // set proper pixel color
  for (uint8_t px = 192; px < 216; px++) {
    strip.setPixelColor(px, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum, BASE_BRIGHTNESS + iterNum);
  }
  strip.show();

  // determine if a direction change is necessary
  if (iterNum >= (RAISED_BRIGHTNESS - BASE_BRIGHTNESS)) {
    _b7uxUp = 0;
  } else if (iterNum <= 0) {
    _b7uxUp = 1;
  }

  // return value based on direction
  if (_b7uxUp == 1) {
    return 2;
  } else if (_b7uxUp == 0) {
    return -2;
  }
  return 0;
}

void resetCmd() {
  for (uint16_t i = 0; i < MAX_CMD_SIZE; i++) {
    cmd[i] = '\0';
  }
  index = 0;
}

void allOff() {
  for (uint16_t px = 0; px < strip.numPixels(); px++) {
    strip.setPixelColor(px, 0, 0, 0);
  }
  strip.show();
}

