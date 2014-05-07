$(function () {
	$('.tonow').each(function (index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.fromNow();
	});
	$('.timestamp').each(function(index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.format('llll');
	});
	$('.timestamp-date').each(function(index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.format('ll');
	});
	$('.timestamp-time').each(function(index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.format('LT');
	});
});

