function drawPieChart(el, dataMap, labels, labelsMap, colors, label_colors) {
    var w = 160;
    var h = 320;
    var outerRadius = w / 2;
    var innerRadius = 0;

    var color = d3.scaleOrdinal().range(colors);
    var labels_color = d3.scaleOrdinal().range(label_colors);
    var total = dataMap.values().reduce(function (prev, curr, idx, arr) { return prev + curr; });

    var svg = d3.select(el)
      .append("svg")
      .attr("width", w)
      .attr("height", h)
      .attr("direction", window.rtl ? "rtl" : "ltr");

    //Draw arc paths
    svg.selectAll("g.pieArc")
      .data(d3.pie()(dataMap.values()))
      .enter()
      .append("g")
      .attr("class", "arc")
      .attr("transform", "translate(" + outerRadius + "," + outerRadius + ")")
      
      .append("path")
      .attr("fill", function(d, i) {
        return color(i);
      })
      .attr("d", d3.arc().innerRadius(innerRadius).outerRadius(outerRadius - 10));

    //Labels
    svg.selectAll("g.pieLabel")
      .data(d3.pie()(dataMap.values()))
      .enter()
      .append("g")
      .attr("class", "arc")
      .attr("transform", "translate(" + outerRadius + "," + outerRadius + ")")

      .append("text")
      .attr("transform", function(d) {
        if (d.value / total >= 0.1) {
          return "translate(" + d3.arc().innerRadius(innerRadius).outerRadius(outerRadius * 1.2).centroid(d) + ")";
        } else {
          return "translate(" + d3.arc().innerRadius(innerRadius).outerRadius(outerRadius * 1.8).centroid(d) + ")";
        }
      })
      .attr("text-anchor", "middle")
      .text(function(d) {return d.value / total >= 0.03 ? (d.value/total * 100).toFixed(0) + '%' : '';})
      .attr('fill', function (d, i) {
        var color = labels_color(i);
        if (d.value / total < 0.1) {
          color = '#000000';
        }
        return color;
      })
      .style('font-size', '9px');

    //Legend
    var legend = svg.append("g")
      .attr("width", w)
      .attr("height", h)
      .selectAll("g")
      .data(color.domain().slice().reverse())
      .enter().append("g")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append("circle")
      .attr("cx", window.rtl ? w - 10 : 10)
      .attr("cy", h/2 + 32)
      .attr("r", 5)
      .style("fill", color.domain(labels));

    //Legend Label
    legend.append("text")
      .data(labels)
      .attr("x", window.rtl ? w - 25 : 25)
      .attr("y", h/2 + 32)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace')
      .text(function(d) { return labelsMap.get(d)});

    //Legend data
    legend.append("text")
      .data(labels)
      .attr("x", window.rtl ? w - 105 : 105)
      .attr("y", h/2 + 32)
      .attr("dy", ".29em")
      .attr("class", "text-monospace")
      .text(function(d) { return '· ' +  dataMap.get(d)});

    var totals = svg.append("g")
      .attr("width", w)
      .attr("height", h/2)
      .selectAll("g")
      .data(color.domain().slice().reverse())
      .enter().append("g")
      .attr("transform", function (d, i) { return "translate(0," + i * 20 + ")"; });

    totals.append("text")
      .data(["Total"])
      .attr("x", window.rtl ? w - 25 : 25)
      .attr("y", h/2 + 32 + (dataMap.values().length + 1) * 16)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace font-weight-bold')
      .text(function (d) { return d });

    totals.append("text")
      .data([total])
      .attr("x", window.rtl ? w - 105 : 105)
      .attr("y", h / 2 + 32 + (dataMap.values().length + 1) * 16)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace font-weight-bold')
      .text(function (d) { return '· ' + d });
}

function drawBarChart(el, dataMap, labels, labelsMap, colors) {
    var margin = { top: 10, right: 40, bottom: 165, left: 0 };
    var width = 160 - margin.left - margin.right;
    var height = 320 - margin.top - margin.bottom;
    var barMargin = 3;

    var color = d3.scaleOrdinal().range(colors);
    var color_rtl = d3.scaleOrdinal().range(colors.slice(0).reverse());
    var labels_rtl = labels.slice(0).reverse();

    var total = dataMap.values().reduce(function (prev, curr, idx, arr) { return prev + curr; });

    var y = d3.scaleLinear().range([height, 0]).domain([0, total]);
    var x = d3.scaleBand().rangeRound([0, width]).align(.1);

    if (window.rtl) {
        var yAxis = d3.axisLeft().scale(y).tickValues([0, total]).tickFormat(d3.format('~s'));
    } else {
        var yAxis = d3.axisRight().scale(y).tickValues([0, total]).tickFormat(d3.format('~s'));
    }

    var chart = d3.select(el)
        .append('svg')
        .attr('width', width + margin.right + margin.left)
        .attr('height', height + margin.top + margin.bottom)
        .attr("direction", (window.rtl ? "rtl" : "ltr"))
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var bar = chart.selectAll('g')
        .data(window.rtl ? labels_rtl : labels)
        .enter().append('g')
        .attr('transform', function (d) { return 'translate(' + x.domain(window.rtl ? labels_rtl : labels)(d) + ', 0)'; });

    bar.append('rect')
        .attr('y', function (d) { return y(dataMap.get(d)); })
        .attr('height', function (d) { return height - y(dataMap.get(d)); })
        .attr('transform', 'translate(' + (window.rtl ? margin.right + margin.left : margin.left) + ',' + margin.top + ')')
        .attr('width', x.domain(window.rtl ? labels_rtl : labels)(window.rtl ? labels_rtl[1] : labels[1]) - barMargin)
        .attr('fill', window.rtl ? color_rtl.domain(labels_rtl) : color.domain(labels));

    bar.append('text')
        .attr('x', (x.domain(window.rtl ? labels_rtl : labels)(window.rtl ? labels_rtl[1] : labels[1]) - barMargin) / 2)
        .attr('y', function (d) { return y(dataMap.get(d)) + 4; })
        .attr('dy', "-.85em")
        .attr('fill', '#222')
        .style('font', '8px sans-serif')
        .attr('text-anchor', 'middle')
        .attr('transform', 'translate(' + (window.rtl ? margin.right + margin.left : margin.left) + ',' + margin.top + ')')
        .text(function (d) { return dataMap.get(d); });

    chart.append('g')
        .attr('class', 'y axis')
        .attr('transform', 'translate(' + (window.rtl ? margin.right : (width + margin.left)) + ',' + margin.top + ')')
        .call(yAxis);

    // Legend
    var legend = chart.append('g')
        .attr('transform', 'translate(0, 40)')
        .attr('width', width)
        .attr('height', height)
        .selectAll('g')
        .data(window.rtl ? color_rtl.range() : color.range())
        .enter().append('g')
        .attr('transform', function (d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append('circle')
        .attr('cx', window.rtl ? width + margin.right + margin.left - 5 : 5)
        .attr('cy', height)
        .attr('r', 5)
        .style('fill', color.domain(labels));

    // Legend Label
    legend.append('text')
        .data(labels)
        .attr('x', window.rtl ? width + margin.right + margin.left - 20 : 20)
        .attr('y', height)
        .attr('dy', '.29em')
        .attr('class', 'text-monospace')
        .text(function (d) { return labelsMap.get(d); });

    // Legend data
    legend.append("text")
        .data(labels)
        .attr("x", window.rtl ? width + margin.right + margin.left - 100 : 100)
        .attr("y", height)
        .attr("dy", ".29em")
        .attr("class", "text-monospace")
        .text(function (d) { return '· ' + dataMap.get(d) });

    var totals = chart.append("g")
        .attr("width", width)
        .attr("height", height)
        .selectAll("g")
        .data(color.range())
        .enter().append("g")
        .attr("transform", function (d, i) { return "translate(0," + i * 20 + ")"; });

    totals.append("text")
        .data(["Total"])
        .attr("x", window.rtl ? width + margin.right + margin.left - 20 : 20)
        .attr("y", height + 40 + (dataMap.values().length + 1) * 16)
        .attr("dy", ".29em")
        .attr('class', 'text-monospace font-weight-bold')
        .text(function (d) { return d });

    totals.append("text")
        .data([total])
        .attr("x", window.rtl ? width + margin.right + margin.left - 100 : 100)
        .attr("y", height + 40 + (dataMap.values().length + 1) * 16)
        .attr("dy", ".29em")
        .attr('class', 'text-monospace font-weight-bold')
        .text(function (d) { return '· ' + d });
}