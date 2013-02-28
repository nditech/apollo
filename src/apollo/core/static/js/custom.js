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

  $('.select2').select2({
    minimumInputLength: 1,
    matcher: function(term, text) { return text.toUpperCase().indexOf(term.toUpperCase()) === 0; }
  });

  $('.select2-locations').select2({
    allowClear: true,
    minimumInputLength: 1,
    loadMorePadding: 5,
    ajax: {
      url: '/api/v2/locations/',
      dataType: 'json',
      quietMillis: 500,
      data: function (term, page) {
        return {
          name__istartswith: term,
          limit: 20,
          offset: (page - 1) * 20
        };
      },
      results: function (data, page) {
        var more = (page * 20) < data.meta.total_count;
        return {results: data.objects, more: more};
      }
    },
    formatResult: function (location, container, query) { return location.name + ' · <i>' + location.type.name + '</i>'; },
    formatSelection: function (location, container) { return location.name + ' · <i>' + location.type.name + '</i>'; },
    escapeMarkup: function(m) { return m; },
    initSelection : function (element, callback) {
      var location_id = element.val();
      if (location_id) {
        var data = {name: element.data('name'), type: {name: element.data('type')}};
        callback(data);
      }
    }
  });

  $('.select2-observers').select2({
    minimumInputLength: 1,
    loadMorePadding: 5,
    ajax: {
      url: '/api/v2/contacts/',
      dataType: 'json',
      quietMillis: 500,
      data: function (term, page) {
        return {
          observer_id__istartswith: term,
          limit: 20,
          offset: (page - 1) * 20
        };
      },
      results: function (data, page) {
        var more = (page * 20) < data.meta.total_count;
        return {results: data.objects, more: more};
      }
    },
    formatResult: function (observer, container, query) { return observer.observer_id + ' · <i>' + observer.name + '</i>'; },
    formatSelection: function (observer, container) { return observer.observer_id + ' · <i>' + observer.name + '</i>'; },
    escapeMarkup: function(m) { return m; }
  });

  // ajax
  jQuery(document).ajaxSend(function(event, xhr, settings) {
      function getCookie(name) {
          var cookieValue = null;
          if (document.cookie && document.cookie !== '') {
              var cookies = document.cookie.split(';');
              for (var i = 0; i < cookies.length; i++) {
                  var cookie = jQuery.trim(cookies[i]);
                  // Does this cookie string begin with the name we want?
                  if (cookie.substring(0, name.length + 1) == (name + '=')) {
                      cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                      break;
                  }
              }
          }
          return cookieValue;
      }
      function sameOrigin(url) {
          // url could be relative or scheme relative or absolute
          var host = document.location.host; // host + port
          var protocol = document.location.protocol;
          var sr_origin = '//' + host;
          var origin = protocol + sr_origin;
          // Allow absolute or scheme relative URLs to same origin
          return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
              (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
              // or any other URL that isn't scheme relative or absolute i.e relative.
              !(/^(\/\/|http:|https:).*/.test(url));
      }
      function safeMethod(method) {
          return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
      }

      if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
          xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      }
  });
});
