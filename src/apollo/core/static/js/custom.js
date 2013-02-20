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
    escapeMarkup: function(m) { return m; }
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
});
