$(function () {
	$('#filter_reset').on('click', function() {
		var $form = $(this).parents('.form-inline');
		$form.find(':input').not('button').each(function() { $(this).val(''); })
		$form.submit();
	});
	$('select.select2').select2();
});