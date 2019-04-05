Release Notes v2.8.1
====================

This release introduces worker-based updates for expensive submission state 
computation. It offloads work from the main web loop when processing 
incoming messages so responses are quicker.

When deploying to production, make sure to size both instances and worker 
concurrency so that, you don't use up all available compute cores and not 
use enough making updates very slow.

Bugs
----

* made a correction on which column the percentage of valid votes is displayed
* removed extraneous permission defaults
* set the submission comment deployment before it is saved
* fixed the output of the byte-order mark in file exports

Features
--------

* switched to using alpine linux v3.7
* added management command for setting up default permissions
* added indexes for sortable columns in the participants list

