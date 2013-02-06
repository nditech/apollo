$(function(){
  $('.dropdown-toggle').dropdown();
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
});