$(function () {
	$('.piechart').each(function() {
		var data = [];
		var element = this;
		var ds = JSON.parse(this.dataset.chart);
		for (prop in ds)
			if (ds.hasOwnProperty(prop) && prop != 'name')
				data.push({label: prop, value: ds[prop]});

		nv.addGraph(function() {
			var chart = nv.models.pieChart()
				.x(function(d) { return d.label; })
				.y(function(d) { return d.value; })
				.width(150)
				.height(150)
				.showLabels(false);

			d3.select(element).datum(data)
				.transition().duration(350)
				.call(chart);

			return chart;
		});
	});
});