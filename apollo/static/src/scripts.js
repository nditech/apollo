"use strict";

import $ from 'jquery';
import './js/app.js';
import bsCustomFileInput from 'bs-custom-file-input';

$(document).ready(function () {
    bsCustomFileInput.init()
});

window.jQuery = $;
window.$ = $;

import 'select2/src/js/jquery.select2.js';
import 'datatables.net-bs4/js/dataTables.bootstrap4.js';
import 'datatables.net-fixedcolumns-bs4/js/fixedColumns.bootstrap4.js';

const Translation = require("select2/src/js/select2/translation");

Translation._cache["en"] = require("select2/src/js/select2/i18n/en");
Translation._cache["es"] = require("select2/src/js/select2/i18n/es");
Translation._cache["fr"] = require("select2/src/js/select2/i18n/fr");
Translation._cache["az"] = require("select2/src/js/select2/i18n/az");
Translation._cache["ar"] = require("select2/src/js/select2/i18n/ar");
Translation._cache["de"] = require("select2/src/js/select2/i18n/de");
Translation._cache["ru"] = require("select2/src/js/select2/i18n/ru");
Translation._cache["ro"] = require("select2/src/js/select2/i18n/ro");

