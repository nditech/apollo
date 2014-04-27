function makeElement(label, is_administrative, is_political) {
    var maxLineLength = _.max(label.split('\n'), function(l) { return l.length; }).length;

    // Compute width/height of the rectangle based on the number 
    // of lines in the label and the letter size. 0.6 * letterSize is
    // an approximation of the monospace font letter width.
    var letterSize = 12;
    var width = 2 * (letterSize * (0.6 * maxLineLength + 1));
    var height = 2 * ((label.split('\n').length + 1) * letterSize);

    return new joint.shapes.basic.Rect({
        label: label,
        is_administrative: is_administrative ? true : false,
        is_political: is_political ? true : false,
        size: { width: width, height: height },
        attrs: {
            text: { text: label, 'font-size': letterSize, 'font-family': "'Helvetica Neue', Helvetica, Arial, sans-serif" },
            rect: {
                width: width, height: height,
                rx: 5, ry: 5,
                stroke: '#555',
            }
        }
    });
}

function makeLink(parentElementId, childElementId) {
    return new joint.dia.Link({
        source: { id: parentElementId },
        target: { id: childElementId },
        attrs: { '.marker-target': { d: 'M 8 0 L 0 4 L 8 8 z' } },
        smooth: true
    });
}

function getChildren(element_id) {
  var childLinks = _.filter(graph.getLinks(), function (link) {
    return link.get('source').id == element_id
  });
  return _.map(_.filter(childLinks, function (child) { return child.get('target').id != undefined; }),
    function (link) { return link.get('target').id; });
}

function getParents(element_id) {
  var parentLinks = _.filter(graph.getLinks(), function (link) {
    return link.get('target').id == element_id
  });
  return _.map(_.filter(parentLinks, function (child) { return child.get('source').id != undefined; }),
    function (link) { return link.get('source').id; });
}

$('#addDivisionModalButton').click(function (ev) {
  $('#addDivisionName').val('');
  $('#addDivisionAdministrative').prop('checked', false);
  $('#addDivisionPolitical').prop('checked', false);
  $('#addDivisionParents').select2('val', '');

  var $el = $('#addDivisionParents');
  $el.empty();
  $.each(graph.getElements(), function(k, v) {
    $el.append($("<option></option>")
      .attr("value", v.id).text(v.get('label')));
  });
  $('#addDivision').modal('show');
});

$('#addDivisionAddButton').click(function (ev) {
  var name = $('#addDivisionName').val();
  var is_administrative = $('#addDivisionAdministrative').prop('checked');
  var is_political = $('#addDivisionPolitical').prop('checked');
  var parent_ids = $('#addDivisionParents').val();

  if (name && !_.find(graph.getElements(), function(elem) { return elem.get('label') == name})) {
    var cells = [];
    var element = makeElement(name, is_administrative, is_political);
    cells.push(element);
    
    _.each(parent_ids, function(parent_id) {
      cells.push(makeLink(parent_id, element.id));
    });

    graph.addCells(cells);
  }

  $('#addDivision').modal('hide');
  return false;
});

$('#updateDivisionDeleteButton').click(function (ev) {
  var element_id = $('#updateDivisionId').val();

  var element = _.find(graph.getElements(), function (el) {
    return el.id == element_id;
  });

  if (element) {
    parents = getParents(element.id);
    children = getChildren(element.id);

    graph.getCell(element.id).remove();

    new_links = [];

    _.each(parents, function (parent) {
      _.each(children, function (child) {
        new_links.push(makeLink(parent, child));
      });
    });

    graph.addCells(new_links);
  }

  $('#updateDivision').modal('hide');
});

$('#updateDivisionUpdateButton').click(function (ev) {
  var element_id = $('#updateDivisionId').val();
  var label = $('#updateDivisionName').val();
  var is_administrative = $('#updateDivisionAdministrative').prop('checked');
  var is_political = $('#updateDivisionPolitical').prop('checked');
  var parents = $('#updateDivisionParents').val();

  var element = _.find(graph.getElements(), function (el) {
    return el.id == element_id;
  });

  if (element) {
    element.get('attrs').text.text = label;
    element.set('label', label);
    element.set('is_administrative', is_administrative);
    element.set('is_political', is_political);

    var maxLineLength = _.max(label.split('\n'), function(l) { return l.length; }).length;
    var letterSize = 12;
    var width = 2 * (letterSize * (0.6 * maxLineLength + 1));
    var height = 2 * ((label.split('\n').length + 1) * letterSize);

    element.resize(width, height);
    element.trigger('change:attrs', element);

    _.each(_.filter(graph.getLinks(), function (link) {
      return link.get('target').id == element.id
    }), function (link) { link.remove(); });

    var new_links = [];
    _.each(parents, function (parent) { new_links.push(makeLink(parent, element.id))});

    graph.addCells(new_links);
  }

  $('#updateDivision').modal('hide');
  return false;
});

$('#save').click(function (ev) {
  $('#divisions_graph').val(JSON.stringify(graph.toJSON()));
});

$('select').select2();

var graph = new joint.dia.Graph;
var paper = new joint.dia.Paper({
    el: $('#paper'),
    width: $('#paper').width(),
    height: 1000,
    gridSize: 1,
    model: graph
});

graph_data = $('#paper').data('graph');

if (graph_data) {
  graph.fromJSON(graph_data);
}

paper.on('cell:pointerdblclick', 
    function(cellView, evt, x, y) {
        $('#updateDivisionName').val(cellView.model.get('label'));
        $('#updateDivisionId').val(cellView.model.id);
        $('#updateDivisionAdministrative').prop('checked', cellView.model.get('is_administrative') ? true : false);
        $('#updateDivisionPolitical').prop('checked', cellView.model.get('is_political') ? true : false);

        $('#updateDivisionParents').empty();

        var parents = [];
        parents.push(cellView.model.id); // add the current element to the list

        var $el = $('#updateDivisionParents');
        $el.empty();
        $.each(_.filter(graph.getElements(), function(el) { return !_.contains(parents, el.id) }), function(k, v) {
          var option = $("<option></option>").attr("value", v.id).text(v.get('label'));
          $el.append(option);
        });

        $('#updateDivisionParents').select2('val', getParents(cellView.model.id));
        $('#updateDivision').modal('show');
    }
);

$('.alert').delay(4000).fadeOut(1000);
