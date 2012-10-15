$(function(){
    $('.dropdown-toggle').dropdown();
    $('a').click(function (e) {
       $(this).tab('show');
    });
    $('.datesel').datepicker()
  		.on('changeDate', function(ev){
    	$(this).datepicker('hide');
  	});
  	$('.datesel input').click(function(){
  		$(this).parent().datepicker('show');
  	});
  });