"use strict";

import $ from 'jquery';
import 'tempusdominus-bootstrap-4/build/js/tempusdominus-bootstrap-4.js';
import 'tempusdominus-bootstrap-4/build/css/tempusdominus-bootstrap-4.css';

$(function () {
    $('#filter_reset').on('click', function () {
        var $form = $(this).parents('form').first();
        $form.find(':input').not('button').each(function () { $(this).val(''); })
        $form.submit();
    });

    $('.tonow').each(function (index) {
        var timestamp = moment.unix(Number($(this).data('timestamp')));
        this.innerText = timestamp.fromNow();
    });
    $('.timestamp').each(function (index) {
        var timestamp = moment.unix(Number($(this).data('timestamp')));
        this.innerText = timestamp.format('llll');
    });
    $('.timestamp-date').each(function (index) {
        var timestamp = moment.unix(Number($(this).data('timestamp')));
        this.innerText = timestamp.format('ll');
    });
    $('.timestamp-time').each(function (index) {
        var timestamp = moment.unix(Number($(this).data('timestamp')));
        this.innerText = timestamp.format('LT');
    });
});