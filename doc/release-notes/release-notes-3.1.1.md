Release Notes v3.1.1
====================

Changelog
---------

* FIX: fixed the timezone conversion for use in filters with a date widget
* FIX: also remove the sample filter option when the filters are reset
* FIX: fixed the rendering of a missing value for histograms
* FIX: fixed broken name search for participants
* FIX: standardized nomenclature for referring to the participant id, supervisor id and location code
* FIX: fixed a few bugs relating to locations importing
* FIX: respect filter parameters when making exports
* FIX: participants list pagination and totals count
* FIX: use the correct attribute when retrieving the last seen phone number of a participant
* FIX: increased worker timeout for gunicorn workers to enable longer-running web requests (like downloads)
* CLEANUP: removed extraneous command line interface commands that have become redundant as a result of the admin web gui
* FEAT: convert the daily progress chart into a table
* FEAT: updated Spanish translation files
* FEAT: updated a few menu item titles (e.g. renamed Account Settings to User Settings)
* FEAT: allow for specifying if an administrative division will contain GPS data
