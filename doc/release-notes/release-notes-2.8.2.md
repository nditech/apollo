Release Notes v2.8.2
====================

This minor release fixes a few bugs with data imports with the major 
bug fix having to do with an issue where subsequent participant data 
uploads simply added more data to the phone number field rather than 
replacing what was previously there.

Bugs
----

* clear phones when uploading new data (#266)
* force sync before running supervisor linking pass (#171)
* supply deployment and phone number for background update of 
  submissions (#173)
