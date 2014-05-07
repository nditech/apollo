$(function () {
	$('.tonow').each(function (index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.fromNow();
	});
});

$(function() {
	$('.timestamp').each(function(index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.format('llll');
	});
});

$(function() {
	$('.timestamp-date').each(function(index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.format('ll');
	});
});

$(function() {
	$('.timestamp-time').each(function(index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.format('LT');
	});
});

