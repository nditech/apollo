  function drawPieChart(el) {
    var w = 160;
    var h = 320;
    var outerRadius = w / 2;
    var innerRadius = 0;

    var json = JSON.parse(el.dataset.chart);
    var data = [json.Missing + (json.Conflict || 0), json.Partial, json.Complete, json.Offline];
    var color = d3.scale.ordinal().range(["#dc3545", "#ffc107", "#28a745", "#aaaaaa"]); // Conflict color #E83992
    var labels_color = d3.scale.ordinal().range(["#ffffff", "#000000", "#ffffff", "#000000"]);
    var labels = ['Missing', 'Partial', 'Complete', 'No Signal']; // Conflict label
    var total = data.reduce(function (prev, curr, idx, arr) { return prev + curr; });

    var svg = d3.select(el)
      .append("svg")
      .attr("width", w)
      .attr("height", h/2)

    //Draw arc paths
    svg.selectAll("g.pieArc")
      .data(d3.layout.pie()(data))
      .enter()
      .append("g")
      .attr("class", "arc")
      .attr("transform", "translate(" + outerRadius + "," + outerRadius + ")")
      
      .append("path")
      .attr("fill", function(d, i) {
        return color(i);
      })
      .attr("d", d3.svg.arc().innerRadius(innerRadius).outerRadius(outerRadius - 10));

    //Labels
    svg.selectAll("g.pieLabel")
      .data(d3.layout.pie()(data))
      .enter()
      .append("g")
      .attr("class", "arc")
      .attr("transform", "translate(" + outerRadius + "," + outerRadius + ")")

      .append("text")
      .attr("transform", function(d) {
        if (d.value / total >= 0.1) {
          return "translate(" + d3.svg.arc().innerRadius(innerRadius).outerRadius(outerRadius * 1.2).centroid(d) + ")";
        } else {
          return "translate(" + d3.svg.arc().innerRadius(innerRadius).outerRadius(outerRadius * 1.8).centroid(d) + ")";
        }
      })
      .attr("text-anchor", "middle")
      .text(function(d) {return d.value / total >= 0.01 ? (d.value/total * 100).toFixed(0) + '%' : '';})
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
      .attr("height", h/2)
      .selectAll("g")
      .data(color.domain().slice().reverse())
      .enter().append("g")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append("circle")
      .attr("cx", 10)
      .attr("cy", h/2 + 32)
      .attr("r", 5)
      .style("fill", color.domain(labels));

    //Legend Label
    legend.append("text")
      .data(labels)
      .attr("x", 25)
      .attr("y", h/2 + 32)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace')
      .text(function(d) { return d});

    //Legend data
    legend.append("text")
      .data(data)
      .attr("x", 105)
      .attr("y", h/2 + 32)
      .attr("dy", ".29em")
      .attr("class", "text-monospace")
      .text(function(d) { return '· ' +  d});

    var totals = svg.append("g")
      .attr("width", w)
      .attr("height", h/2)
      .selectAll("g")
      .data(color.domain().slice().reverse())
      .enter().append("g")
      .attr("transform", function (d, i) { return "translate(0," + i * 20 + ")"; });

    totals.append("text")
      .data(["Total"])
      .attr("x", 25)
      .attr("y", h/2 + 32 + (data.length + 1) * 16)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace font-weight-bold')
      .text(function (d) { return d });

    totals.append("text")
      .data([total])
      .attr("x", 105)
      .attr("y", h / 2 + 32 + (data.length + 1) * 16)
      .attr("dy", ".29em")
      .attr('class', 'text-monospace font-weight-bold')
      .text(function (d) { return '· ' + d });
  }

  $(function () {
    $('.piechart').each(function(idx, el) {
      drawPieChart(el);
    });
  });