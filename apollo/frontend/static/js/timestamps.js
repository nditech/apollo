$(function () {
	$('.tonow').each(function (index) {
		var timestamp = moment.unix(Number.parseInt(this.innerText));
		this.innerText = timestamp.fromNow();
	});
});