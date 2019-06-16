"use strict";

import $ from 'jquery';
import './js/app.js';
import 'select2/dist/js/select2.js';
import bsCustomFileInput from 'bs-custom-file-input';

$(document).ready(function () {
    bsCustomFileInput.init()
});

window.jQuery = $;
window.$ = $;