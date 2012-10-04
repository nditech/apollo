$(function(){
    $('.dropdown-toggle').dropdown();
    $('a').click(function (e) {
      e.preventDefault();
      $(this).tab('show');
    })
  }); 