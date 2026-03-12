/*
 * ARDUINO TRAFFIC SIGNAL CONTROLLER
 * Team Ryzen_4090Ti
 *
 * Receives serial commands from Python and controls LEDs.
 * Protocol: "N:G,S:R,E:R,W:R\n"
 *   N/S/E/W = Lane direction
 *   G = Green, R = Red, Y = Yellow
 *
 * Wiring (4 lanes x 3 LEDs = 12 pins):
 *   North: RED=2, YELLOW=3, GREEN=4
 *   South: RED=5, YELLOW=6, GREEN=7
 *   East:  RED=8, YELLOW=9, GREEN=10
 *   West:  RED=11, YELLOW=12, GREEN=13
 */

int lanes[4][3] = {
    {2, 3, 4},   // North: RED, YELLOW, GREEN
    {5, 6, 7},   // South
    {8, 9, 10},  // East
    {11, 12, 13} // West
};

void setup()
{
  Serial.begin(9600);

  // Set all LED pins as OUTPUT
  for (int i = 0; i < 4; i++)
  {
    for (int j = 0; j < 3; j++)
    {
      pinMode(lanes[i][j], OUTPUT);
    }
  }

  // Start with all RED
  allRed();
}

void loop()
{
  if (Serial.available())
  {
    String data = Serial.readStringUntil('\n');
    data.trim();
    if (data.length() > 0)
    {
      parseAndSet(data);
    }
  }
}

void parseAndSet(String data)
{
  // Parse "N:G,S:R,E:R,W:R"
  int laneIndex = 0;
  int start = 0;

  for (int i = 0; i <= (int)data.length(); i++)
  {
    if (i == (int)data.length() || data[i] == ',')
    {
      if (i - start >= 3)
      {
        String part = data.substring(start, i);
        char state = part.charAt(2); // G, R, or Y
        if (laneIndex < 4)
        {
          setLane(laneIndex, state);
        }
        laneIndex++;
      }
      start = i + 1;
    }
  }
}

void setLane(int lane, char state)
{
  // Turn off all LEDs for this lane first
  for (int j = 0; j < 3; j++)
  {
    digitalWrite(lanes[lane][j], LOW);
  }

  // Turn on the correct LED
  switch (state)
  {
  case 'R':
    digitalWrite(lanes[lane][0], HIGH);
    break; // RED
  case 'Y':
    digitalWrite(lanes[lane][1], HIGH);
    break; // YELLOW
  case 'G':
    digitalWrite(lanes[lane][2], HIGH);
    break; // GREEN
  }
}

void allRed()
{
  for (int i = 0; i < 4; i++)
  {
    setLane(i, 'R');
  }
}
