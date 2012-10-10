$(function(){
    $('.dropdown-toggle').dropdown();
    $('a').click(function (e) {
       $(this).tab('show');
    });
    $('.datesel').datepicker()
  		.on('changeDate', function(ev){
    	$(this).datepicker('hide');
  	});
  	$('.datesel input').click(function(){
  		$(this).parent().datepicker('show');
  	});
  });

var chart;
    
    $(function () {
      
      // Build the chart
        chart = new Highcharts.Chart({
            chart: {
                renderTo: 'setup',
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false
            },
            title: {
                text: ''
            },
            tooltip: {
              pointFormat: '{series.name}: <b>{point.percentage}%</b>',
              percentageDecimals: 1
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false
                    },
                    showInLegend: true
                }
            },
            series: [{
                type: 'pie',
                name: 'Status',
                data: [
                    ['Partial', 50],
                    ['Missing', 50],
                    ['Complete', 50]
                ],
                color: 'red'
            }]
        });
    });

var chart;
    
    $(function () {
      
      // Build the chart
        chart = new Highcharts.Chart({
            chart: {
                renderTo: 'voting',
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false
            },
            title: {
                text: ''
            },
            tooltip: {
              pointFormat: '{series.name}: <b>{point.percentage}%</b>',
              percentageDecimals: 1
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false
                    },
                    showInLegend: true
                }
            },
            series: [{
                type: 'pie',
                name: 'Status',
                data: [
                    ['Partial', 20],
                    ['Missing', 30],
                    ['Complete', 40]
                ],
                color: 'red'
            }]
        });
    });
var chart;
    
    $(function () {
      
      // Build the chart
        chart = new Highcharts.Chart({
            chart: {
                renderTo: 'counting',
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false
            },
            title: {
                text: ''
            },
            tooltip: {
              pointFormat: '{series.name}: <b>{point.percentage}%</b>',
              percentageDecimals: 1
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false
                    },
                    showInLegend: true
                }
            },
            series: [{
                type: 'pie',
                name: 'Status',
                data: [
                    ['Partial', 30],
                    ['Missing', 80],
                    ['Complete', 30]
                ],
                color: 'red'
            }]
        });
    });
var chart;
    
    $(function () {
      
      // Build the chart
        chart = new Highcharts.Chart({
            chart: {
                renderTo: 'closing',
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false
            },
            title: {
                text: ''
            },
            tooltip: {
              pointFormat: '{series.name}: <b>{point.percentage}%</b>',
              percentageDecimals: 1
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false
                    },
                    showInLegend: true
                }
            },
            series: [{
                type: 'pie',
                name: 'Status',
                data: [
                    ['Missing', 45.0],
                    ['Partial', 26.8],
                    ['Complete', 12.8]
                ],
                color: 'red'
            }]
        });
    });