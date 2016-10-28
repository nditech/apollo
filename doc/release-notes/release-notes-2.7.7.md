Release Notes v2.7.7
===================

Features
--------
* Added translation strings for Romanian
* Updated the translation strings for French
* Added an application setting to enable turning off/on translations of the I, L and O characters in text messages.
* Added support for parsing multi-line text messages
* Added support for blocking parsing of incoming messages on a telerivet phone that originated from that phone. This would prevent the problem we have with infinite messaging loops because a phone is "texting itself"
* Added support for more expressions in computing conditions in quality assurance tests. These expressions include boolean values (True or False), comparison operators (>, >=, <=, <) and the inequality operator (!=)
* Added support for transliterating input. This will help solve problems involving non-latin characters that look like latin alphabets and cause confusion when they cannot be parsed in text inputs.
* Added support for transliterating output. Due to some handsets/cell networks being unable to handle accented or non-latin characters, this converts those characters into plain ascii so the messages can be displayed correctly.

Bugs
----
* Fixed a bug that prevented the display of messages that were not included in overlapping events because they did not fall within the current day (this only affects past events). The solution was to ensure that the selected event is included when retrieve messages in an event.

Improvements
------------
* Switched to installing uwsgi from the package index so as to have more predictable docker builds rather than compiling and having unpredictable success in doing so.
* Added better test coverage for quality assurance test conditions.