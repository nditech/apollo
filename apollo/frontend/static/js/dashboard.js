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
				.x(function(d) { return d.label; })
				.y(function(d) { return d.value; })
				.width(400)
				.height(400)
				.color(['#4e9a06', '#c00', '#f57900'])
				.showLabels(false);

			d3.select(element).datum(data)
				.transition().duration(350)
				.attr('height', 400)
				.attr('width', 400)
				.call(chart);

			return chart;
		});
	});
});