$(function(){
  $('.dropdown-toggle').dropdown();
  $('abbr').tooltip();
  $('.table-fixed-header').fixedHeader();
  $('.dropdown-toggle a').click(function (e) {
     $(this).tab('show');
  });
  $('.datesel').datepicker()
    .on('changeDate', function(ev){
    $(this).datepicker('hide');
  });
  $('.datesel input').click(function(){
    $(this).parent().datepicker('show');
  });
  $('.form-reset').click(function (){
    form = $(this).parents('form');
    $('input[name!="csrfmiddlewaretoken"]', form).each(function (id, el) { $(el).val(""); });
    $('select', form).each(function (id, el) { $(el).val(""); });
    $(form).submit();
  });
  $('select.select2').select2({
    minimumInputLength: 1,
    matcher: function(term, text) { return text.toUpperCase().indexOf(term.toUpperCase()) === 0; }
  });

  function _safe(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') ;
  }

  function locationsOptionsString() {
    return {
      minimumInputLength: 1,
      loadMorePadding: 5,
      placeholder: 'Location',
      ajax: {
        url: '/api/locations/',
        dataType: 'json',
        quietMillis: 500,
        data: function (term, page) {
          return {
            q: term,
            limit: 20,
            offset: (page - 1) * 20
          };
        },
        results: function (data, page) {
          var more = (page * 20) < data.meta.total;
          return {results: data.objects, more: more};
        }
      },
      formatResult: function (location, container, query) { return _safe(location.name) + ' · <i>' + _safe(location.location_type) + '</i>'; },
      formatSelection: function (location, container) { return _safe(location.name) + ' · <i>' + _safe(location.location_type) + '</i>'; },
      escapeMarkup: function(m) { return m; },
      initSelection : function (element, callback) {
        var location_id = element.val();
        if (location_id && element.data('name') && element.data('location_type')) {
          var data = {name: element.data('name'), location_type: element.data('location_type')};
          callback(data);
        }
      }
    };
  }

  var locations_select2_options = locationsOptionsString();
  var locations_select2_clearable_options = locationsOptionsString();
  locations_select2_clearable_options.allowClear = true;

  $('input.select2-locations').select2(locations_select2_options);
  $('input.select2-locations-clear').select2(locations_select2_clearable_options);

  function observerOptions() {
    return {
      minimumInputLength: 1,
      loadMorePadding: 5,
      placeholder: 'Participant',
      ajax: {
        url: '/api/participants/',
        dataType: 'json',
        quietMillis: 500,
        data: function (term, page) {
          return {
            q: term,
            limit: 20,
            offset: (page - 1) * 20
          };
        },
        results: function (data, page) {
          var more = (page * 20) < data.meta.total;
          return {results: data.objects, more: more};
        }
      },
      formatResult: function (observer, container, query) { return _safe(observer.participant_id) + ' · <i>' + _safe(observer.name) + '</i>'; },
      formatSelection: function (observer, container) { return _safe(observer.participant_id) + ' · <i>' + _safe(observer.name) + '</i>'; },
      escapeMarkup: function(m) { return m; },
      initSelection : function (element, callback) {
        var location_id = element.val();
        if (location_id && element.data('name') && element.data('participant_id')) {
          var data = {name: element.data('name'), participant_id: element.data('participant_id')};
          callback(data);
        }
      }
    };
  }

  var observer_select2_options = observerOptions();
  var observer_select2_clearable_options = observerOptions();
  observer_select2_clearable_options.allowClear = true;

  $('input.select2-observers').select2(observer_select2_options);
  $('input.select2-observers-clear').select2(observer_select2_clearable_options);
});
