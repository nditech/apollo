$(function () {
	$('#select_all').on('click', function() {
		var toggleState = this.checked;
		$("input[name='ids']").each(function(index) {
			this.checked = toggleState;
		});
	});
});