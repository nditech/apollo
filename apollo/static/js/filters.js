$(function () {
	$('#filter_reset').on('click', function() {
		var $form = $(this).parents('form').first();
		$form.find(':input').not('button').each(function() { $(this).val(''); })
		$form.submit();
	});
	$('select.select2').select2();
});