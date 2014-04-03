$(function () {
	$('.piechart').each(function() {
		var data = [];
		var element = this;
		var ds = JSON.parse(element.dataset.chart);
		for (prop in ds)
			if (ds.hasOwnProperty(prop) && prop != 'name')
				data.push({label: prop, value: ds[prop]});

		nv.addGraph(function() {
			var chart = nv.models.pieChart()
				.x(function(d) { return d.label + ' (' + d.value + ')'; })
				.y(function(d) { return d.value; })
				.valueFormat(d3.format('^d'))
				.color(['#4e9a06', '#c00', '#f57900'])
				.margin({top: 40, bottom: 40, left: 15, right: 15})
				.showLabels(false);

			d3.select(element).datum(data)
				.transition().duration(350)
				.call(chart);

			return chart;
		});
	});
});