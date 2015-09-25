  function drawPieChart(el) {
    var w = 140;
    var h = 300;
    var outerRadius = w / 2;
    var innerRadius = 0;
    
    var json = JSON.parse(el.dataset.chart);
    var data = [json.Missing, json.Partial, json.Complete];
    var color = d3.scale.ordinal().range(["#FF5200", "#FFE22B", "#3BDF4A"]); // Conflict color #E83992
    var labels = ['Missing', 'Partial', 'Complete']; // Conflict label
    var total = data.reduce(function (prev, curr, idx, arr) { return prev + curr; });

    function number_format(num) {
      if (num.toFixed(0) == num || num < 1)
        return num.toFixed(0);
      else
        return num.toFixed(1);
    }

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
      .attr("d", d3.svg.arc().innerRadius(innerRadius).outerRadius(outerRadius));

    //Labels
    svg.selectAll("g.pieLabel")
      .data(d3.layout.pie()(data))
      .enter()
      .append("g")
      .attr("class", "arc")
      .attr("transform", "translate(" + outerRadius + "," + outerRadius + ")")

    
      .append("text")
      .attr("transform", function(d) {
        return "translate(" + d3.svg.arc().innerRadius(innerRadius).outerRadius(outerRadius).centroid(d) + ")";
      })
      .attr("text-anchor", "middle")
      .text(function(d) {return (d.value/total * 100).toFixed(0) + '%';})
      .style('font-size', '10px');

    //Legend
    var legend = svg.append("g")
      .attr("width", w)
      .attr("height", h /4)
      .selectAll("g")
      .data(color.domain().slice().reverse())
      .enter().append("g")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append("circle")
      .attr("cx", w/4 - 26)
      .attr("cy", h/2 + 24)
      .attr("r", 5)
      .style("fill", color.domain(labels));

    //Legend Label
    legend.append("text")
      .data(labels)
      .attr("x", w/4 - 16)
      .attr("y", h/2 + 24)
      .attr("dy", ".35em")
      .style('font-family', 'courier')
      .text(function(d) { return d})
      .style('font-size', '12.5px');

    //Legend data
    legend.append("text")
      .data(data)
      .attr("x", w /2 + 15)
      .attr("y", h/2 + 24)
      .attr("dy", ".35em")
      .style('font-family', 'courier')
      .text(function(d) { return '· ' +  d})
      .style('font-size', '12.5px');
  }

  $(function () {
    $('.piechart').each(function(idx, el) {
      drawPieChart(el);
    });
  });