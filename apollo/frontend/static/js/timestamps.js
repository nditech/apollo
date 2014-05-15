$(function () {
	$('.tonow').each(function (index) {
		var timestamp = moment.unix(Number($(this).data('timestamp')));
		this.innerText = timestamp.fromNow();
	});
	$('.timestamp').each(function(index) {
		var timestamp = moment.unix(Number($(this).data('timestamp')));
		this.innerText = timestamp.format('llll');
	});
	$('.timestamp-date').each(function(index) {
		var timestamp = moment.unix(Number($(this).data('timestamp')));
		this.innerText = timestamp.format('ll');
	});
	$('.timestamp-time').each(function(index) {
		var timestamp = moment.unix(Number($(this).data('timestamp')));
		this.innerText = timestamp.format('LT');
	});
});

