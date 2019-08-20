function drawPieChart(el, dataMap, labels, labelsMap, colors, label_colors, total_label) {
    var w = 160;
    var h = 320;
    var outerRadius = (w + 30) / 2 - 7;
    var innerRadius = 0;

    var color = d3.scaleOrdinal().range(colors);
    var labels_color = d3.scaleOrdinal().range(label_colors);
    var total = dataMap.values().reduce(function (prev, curr, idx, arr) { return prev + curr; });

    var pieData = [];
    labels.forEach(function (label) {
      pieData.push(dataMap.get(label));
    })

    var svg = d3.select(el)
      .append("svg")
      .attr("width", w + 30)
      .attr("height", h)
      .attr("direction", window.rtl ? "rtl" : "ltr");

    //Draw arc paths
    svg.selectAll("g.pieArc")
      .data(d3.pie()(pieData))
      .enter()
      .append("g")
      .attr("class", "arc")
      .attr("transform", "translate(" + (outerRadius + 7) + "," + outerRadius + ")")
      
      .append("path")
      .attr("fill", function(d, i) {
        return color(i);
      })
      .attr("d", d3.arc().innerRadius(innerRadius).outerRadius(outerRadius - 10));

    //Labels
    svg.selectAll("g.pieLabel")
      .data(d3.pie()(pieData))
      .enter()
      .append("g")
      .attr("class", "arc")
      .attr("transform", "translate(" + (outerRadius + 7) + "," + outerRadius + ")")

      .append("text")
      .attr("transform", function(d) {
        if (d.value / total >= 0.1) {
          return "translate(" + d3.arc().innerRadius(innerRadius).outerRadius(outerRadius * 1.2).centroid(d) + ")";
        } else {
          return "translate(" + d3.arc().innerRadius(innerRadius).outerRadius(outerRadius * 1.85).centroid(d) + ")";
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
      .attr("cx", window.rtl ? w - 20 + 30 : 20)
      .attr("cy", h/2 + 32)
      .attr("r", 5)
      .style("fill", color.domain(labels));

    //Legend Label
    legend.append("text")
      .data(labels)
      .attr("x", window.rtl ? w - 35 + 30 : 35)
      .attr("y", h/2 + 32)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace')
      .text(function(d) { return labelsMap.get(d)});

    //Legend data
    legend.append("text")
      .data(labels)
      .attr("x", window.rtl ? (w - (125 - (numDigits(total) * 10))) : 155 - (numDigits(total) * 10))
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
      .data([total_label])
      .attr("x", window.rtl ? w - 35 + 30 : 35)
      .attr("y", h/2 + 32 + (dataMap.values().length + 1) * 16)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace font-weight-bold')
      .text(function (d) { return d });

    totals.append("text")
      .data([total])
      .attr("x", window.rtl ? (w - (135 - 30 + (numDigits(total) * 10))) : 155 - (numDigits(total) * 10))
      .attr("y", h / 2 + 32 + (dataMap.values().length + 1) * 16)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace font-weight-bold')
      .text(function (d) { return '· ' + d });
}

function drawBarChart(el, dataMap, labels, labelsMap, colors, total_label) {
    var width = 160;
    var height = 320;
    var barMargin = 3;
    var topMargin = 10;
    var leftMargin = 15;
    var rightMargin = 15;

    var color = d3.scaleOrdinal().range(colors);
    var color_rtl = d3.scaleOrdinal().range(colors.slice(0).reverse());
    var labels_rtl = labels.slice(0).reverse();

    var total = dataMap.values().reduce(function (prev, curr, idx, arr) { return prev + curr; });

    var y = d3.scaleLinear().range([height/2 - topMargin, 0]).domain([0, total]);
    var x = d3.scaleBand().rangeRound([0, width - leftMargin]).align(.1);

    if (window.rtl) {
        var yAxis = d3.axisLeft().scale(y).tickValues([0, total]).tickFormat(d3.format('~s'));
    } else {
        var yAxis = d3.axisRight().scale(y).tickValues([0, total]).tickFormat(d3.format('~s'));
    }

    var chart = d3.select(el)
        .append('svg')
        .attr('width', width + 30)
        .attr('height', height)
        .attr("direction", (window.rtl ? "rtl" : "ltr"))
        //.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var bar = chart.selectAll('g')
        .data(window.rtl ? labels_rtl : labels)
        .enter().append('g')
        .attr('transform', function (d) { return 'translate(' + (x.domain(window.rtl ? labels_rtl : labels)(d) + leftMargin) + ', 0)'; });

    // Bars
    bar.append('rect')
        .attr('y', function (d) { return y(dataMap.get(d)) + topMargin; })
        .attr('height', function (d) { return (height/2 - topMargin) - y(dataMap.get(d)); })
        .attr('transform', 'translate(' + (window.rtl ? leftMargin + barMargin: 0) + ',0)')
        .attr('width', x.domain(window.rtl ? labels_rtl : labels)(window.rtl ? labels_rtl[1] : labels[1]) - barMargin)
        .attr('fill', window.rtl ? color_rtl.domain(labels_rtl) : color.domain(labels));

    bar.append('text')
        .attr('x', (x.domain(window.rtl ? labels_rtl : labels)(window.rtl ? labels_rtl[1] : labels[1]) - barMargin) / 2 + (window.rtl ? leftMargin + barMargin : 0))
        .attr('y', function (d) { return y(dataMap.get(d)) + 4; })
        .attr('dy', "-.85em")
        .attr('fill', '#222')
        .style('font', '8px sans-serif')
        .attr('text-anchor', 'middle')
        .attr('transform', 'translate(' + (window.rtl ? 0 : 0) + ',' + topMargin + ')')
        .text(function (d) { return dataMap.get(d); });

    // Axis
    chart.append('g')
        .attr('class', 'y axis')
        .attr('transform', 'translate(' + (window.rtl ? leftMargin * 2 : (width)) + ',' + (topMargin - 1) + ')')
        .call(yAxis);

    // Legend
    var legend = chart.append('g')
        .attr('transform', 'translate(0, 0)')
        .attr('width', width)
        .attr('height', height/2)
        .selectAll('g')
        .data(window.rtl ? color_rtl.range() : color.range())
        .enter().append('g')
        .attr('transform', function (d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append('circle')
        .attr('cx', window.rtl ? width - 20 + rightMargin + leftMargin : 20)
        .attr('cy', height/2 + 32)
        .attr('r', 5)
        .style('fill', color.domain(labels));

    // Legend Label
    legend.append('text')
        .data(labels)
        .attr('x', window.rtl ? width - 35 + rightMargin + leftMargin : 35)
        .attr('y', height/2 + 32)
        .attr('dy', '.29em')
        .attr('class', 'text-monospace')
        .text(function (d) { return labelsMap.get(d); });

    // Legend data
    legend.append("text")
        .data(labels)
        .attr("x", window.rtl ? (width - (125 - (numDigits(total) * 10))) : 155 - (numDigits(total) * 10))
        .attr("y", height/2 + 32)
        .attr("dy", ".29em")
        .attr("class", "text-monospace")
        .text(function (d) { return '· ' + dataMap.get(d) });

    var totals = chart.append("g")
        .attr("width", width)
        .attr("height", height/2)
        .selectAll("g")
        .data(color.range())
        .enter().append("g")
        .attr("transform", function (d, i) { return "translate(0," + i * 20 + ")"; });

    totals.append("text")
        .data([total_label])
        .attr("x", window.rtl ? width - 35 + rightMargin + leftMargin : 35)
        .attr("y", height/2 + 32 + (dataMap.values().length + 1) * 16)
        .attr("dy", ".29em")
        .attr('class', 'text-monospace font-weight-bold')
        .text(function (d) { return d });

    totals.append("text")
        .data([total])
        .attr("x", window.rtl ? (width - (125 - (numDigits(total) * 10))) : 155 - (numDigits(total) * 10))
        .attr("y", height/2 + 32 + (dataMap.values().length + 1) * 16)
        .attr("dy", ".29em")
        .attr('class', 'text-monospace font-weight-bold')
        .text(function (d) { return '· ' + d });
}

function numDigits(number) {
  return parseInt(Math.log(number) / Math.log(10));
}