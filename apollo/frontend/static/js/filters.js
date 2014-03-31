$(function () {
	$('#filter_reset').on('click', function() {
		var form = $(this).parent();
		form.find(':input').not('button').each(function() { $(this).val(''); })
		form.submit();
	});
});