# spotify-slack-sync-fredagslistan

## TODO
  - Kollar på att bygga om Jonas Fredags lista grej till till en egen funktion som kör bara på fredagar och typ var 10 minut
  - jämför vad som ligger i listan och adderar bara det som är nytt
  - skriva den i typescript med tester
  - skaffa en spotify token som gäller hela tiden
  - skaffa en slack token för att kolla vad som finns i listan
  - dra ner allt i slack (som skrivits idag)
  - dra ner allt från fredagslistan (som adderats idag)
  - jämföra dom två listorna med varandra
  - ta bort allt som är samma ...
  - skicka upp det som finns kvar i array'en till spotify

  Check spotify token
  Check slack token

  Get list from today in slack
  Get list from spotify
  Compare both lists

  Check if there is a playlist for today in spotify
    - If there is no playlist for today, create a new playlist, save the ID in a variable
    - If there is a playlist already save the id in a variable

  Add the remaning array to spotify playlist

  Announce the playlist in slack (only do this once per day)
  - Maybe add comment in thread about the number of added songs each time it runs.

