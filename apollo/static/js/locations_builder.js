var App = function (languages) {
  var appRef = this;
  appRef.LETTER_SIZE = 12;

  
  var getDefaultName = function (nameTranslations) {
    var fallbackLanguageCode = 'en';

    if (languages.length == 0)
      return nameTranslations[fallbackLanguageCode];
    else
      return nameTranslations[languages[0]];
  };

  appRef.getElementSize = function(theText) {
    // Compute width/height of the rectangle based on the number 
    // of lines in the text and the letter size. 0.6 * the letter size is
    // an approximation of the monospace font letter width.
    var maxLineLength = _.max(theText.split('\n'), function(l) { return l.length; }).length;
    var width = 2 * (appRef.LETTER_SIZE * (0.6 * maxLineLength + 1));
    var height = 2 * ((theText.split('\n').length + 1) * appRef.LETTER_SIZE);

    return {width: width, height: height};
  };

  appRef.addDivision = function (id, name, nameTranslations, isAdministrative, isPolitical, hasRegisteredVoters) {
    var elementSize = appRef.getElementSize(name);

    var shapeOptions = {
      name: name,
      nameTranslations: nameTranslations,
      is_administrative: isAdministrative ? true : false,
      is_political: isPolitical ? true : false,
      has_registered_voters: hasRegisteredVoters ? true : false,
      size: { width: elementSize.width, height: elementSize.height },
      attrs: {
        text: { text: name, 'font-size': appRef.LETTER_SIZE, 'font-family': "'Helvetica Neue', Helvetica, Arial, sans-serif" },
        rect: {
          width: elementSize.width, height: elementSize.height,
          rx: 5, ry: 5,
          stroke: '#708090',
          strokeWidth: 2,
          fill: '#f0f8ff'
        }
      }
    };

    if (id)
      shapeOptions.id = id;

    return new joint.shapes.basic.Rect(shapeOptions);
  };

  appRef.addLink = function(sourceId, targetId) {
    return new joint.dia.Link({
      source: {id: sourceId},
      target: {id: targetId},
      attrs: { '.marker-target': { d: 'M 8 0 L 0 4 L 8 8 z' } },
      smooth: true
    });
  };

  appRef.getChildren = function (element_id) {
    var graph = appRef.paper.model;
    var childLinks = _.filter(graph.getLinks(), function (link) {
      return (link.get('source').id == element_id) && (link.get('target').id != undefined);
    });
    return _.map(childLinks, function (link) { return link.get('target').id; });
  };

  appRef.getParents = function (element_id) {
    var graph = appRef.paper.model;
    var parentLinks = _.filter(graph.getLinks(), function (link) {
      return (link.get('target').id == element_id) && (link.get('source').id != undefined);
    });

    return _.map(parentLinks, function (link) { return link.get('source').id; });
  };

  appRef.layout = function() {
    var paper = appRef.paper;
    var graph = paper.model;
    joint.layout.DirectedGraph.layout(graph, {
      nodeSep: 50,
      edgeSep: 80,
      rankDir: 'TB',
      marginX: 50,
      marginY: 50,
    });
  };

  appRef.init = function() {
  // this.init = function(options) {
    var paperElement = $('#paper');
    var data = paperElement.data('graph');
    // set up graph here
    appRef.paper = new joint.dia.Paper({
      el: paperElement,
      width: paperElement.width(),
      height: 1000,
      model: new joint.dia.Graph,
      // el: options.el,
      // width: options.width,
      // height: options.height,
      gridSize: 1
    }).on({'cell:pointerclick': appRef.launchUpdateModal});

    // init graph cells
    if (data) {
      var cells = [];

      _.each(data.nodes, function(node) {
        cells.push(appRef.addDivision(node.id, node.name, node.nameTranslations, node.is_administrative, node.is_political, node.has_registered_voters));
      });
      _.each(data.edges, function(edge) {
        cells.push(appRef.addLink(edge[0], edge[1]));
      });

      appRef.paper.model.addCells(cells);
      appRef.layout();
    }

    // set up jQuery handlers
    $('#addDivisionButton').click(appRef.launchAddModal);
    $('#addModalSaveButton').click(appRef.saveNewDivision);
    $('#updateModalDeleteButton').click(appRef.deleteDivision);
    $('#updateModalSaveButton').click(appRef.updateDivision);
    $('#save').click(appRef.saveGraph);

    // set up new division modal
    $('#addDivision').on('shown.bs.modal', function () {
      $('#addDivisionName').focus();
    });      

    // initialize select2
    $('select').select2();
  };

  appRef.saveGraph = function(ev) {
    var serializableGraph = {edges: [], nodes: []};
    var graph = appRef.paper.model;
    _.each(graph.getElements(), function(cell) {
      serializableGraph.nodes.push(cell.attributes);
    });
    _.each(graph.getLinks(), function(link) {
      serializableGraph.edges.push([link.attributes.source.id, link.attributes.target.id]);
    });

    $('#divisions_graph').val(JSON.stringify(serializableGraph));
  };

  appRef.launchUpdateModal = function(cellView) {
    var graph = appRef.paper.model;
    var nameTranslations = cellView.model.get('nameTranslations');

    _.each(languages, function (language) {
      var nameSelector = '#updateDivisionName_' + language;
      $(nameSelector).val(nameTranslations[language]);
    });

    $('#updateDivisionId').val(cellView.model.id);
    $('#updateDivisionAdministrative').prop('checked', cellView.model.get('is_administrative') ? true : false);
    $('#updateDivisionPolitical').prop('checked', cellView.model.get('is_political') ? true : false);
    $('#updateDivisionRegisteredVoters').prop('checked', cellView.model.get('has_registered_voters') ? true : false);

    $('#updateDivisionParents').empty();

    var parents = [];
    parents.push(cellView.model.id); // add the current element to the list

    var $el = $('#updateDivisionParents');
    $el.empty();
    $.each(_.filter(graph.getElements(), function(el) { return !_.includes(parents, el.id) }), function(k, v) {
      var option = $("<option></option>").attr("value", v.id).text(v.get('name'));
      $el.append(option);
    });

    $('#updateDivisionParents').select2('val', appRef.getParents(cellView.model.id));
    $('#updateDivision').modal('show');
  };

  appRef.launchAddModal = function() {
    var graph = appRef.paper.model;
    $('#addDivisionAdministrative').prop('checked', false);
    $('#addDivisionPolitical').prop('checked', false);
    $('#addDivisionParents').select2('val', '');

    var $el = $('#addDivisionParents');
    $el.empty();
    $.each(graph.getElements(), function(k, v) {
      $el.append($("<option></option>")
        .attr("value", v.id).text(v.get('name')));
    });
    $('#addDivision').modal('show');
  };

  appRef.saveNewDivision = function() {
    var graph = appRef.paper.model;
    var nameTranslations = {};

    _.each(languages, function (language) {
      var nameSelector = '#addDivisionName_' + language;
      nameTranslations[language] = $(nameSelector).val();
    });
  
    var name = getDefaultName(nameTranslations);

    var is_administrative = $('#addDivisionAdministrative').prop('checked');
    var is_political = $('#addDivisionPolitical').prop('checked');
    var has_registered_voters = $('#addDivisionRegisteredVoters').prop('checked');
    var parent_ids = $('#addDivisionParents').val();

    if (name && !_.find(graph.getElements(), function(elem) { return elem.get('name') == name})) {
      var cells = [];
      var element = appRef.addDivision(null, name, nameTranslations, is_administrative, is_political, has_registered_voters);
      cells.push(element);

      _.each(parent_ids, function(parent_id) {
        cells.push(appRef.addLink(parent_id, element.id));
      });

      graph.addCells(cells);
      appRef.layout();
    }

    $('#addDivision').modal('hide');
    return false;
  };

  appRef.deleteDivision = function() {
    var graph = appRef.paper.model;
    var cellId = $('#updateDivisionId').val();

    var cell = graph.getCell(cellId);

    if (cell) {
      parents = appRef.getParents(cell.attributes.id);
      children = appRef.getChildren(cell.attributes.id);

      cell.remove();

      new_links = [];

      _.each(parents, function (parent) {
        _.each(children, function (child) {
          new_links.push(appRef.addLink(parent, child));
        });
      });

      graph.addCells(new_links);
      appRef.layout();
    }

    $('#updateDivision').modal('hide');
  };

  appRef.updateDivision = function() {
    var graph = appRef.paper.model;
    // load id and (possibly updated) attributes from form
    var cellId = $('#updateDivisionId').val();
    var nameTranslations = {};
    _.each(languages, function (language) {
      var nameSelector = '#updateDivisionName_' + language;
      nameTranslations[language] = $(nameSelector).val()
    });

    var name = getDefaultName(nameTranslations);
    var is_administrative = $('#updateDivisionAdministrative').prop('checked');
    var is_political = $('#updateDivisionPolitical').prop('checked');
    var has_registered_voters = $('#updateDivisionRegisteredVoters').prop('checked');
    var parents = $('#updateDivisionParents').val();

    var cell = graph.getCell(cellId);
    if (cell) {
      cell.attr({text: {text: name}});
      cell.set('nameTranslations', nameTranslations);
      cell.set('is_administrative', is_administrative);
      cell.set('is_political', is_political);
      cell.set('has_registered_voters', has_registered_voters);

      var elementSize = appRef.getElementSize(name);

      cell.resize(elementSize.width, elementSize.height);

      _.each(_.filter(graph.getLinks(), function (link) {
        return link.get('target').id == cell.id
      }), function (link) { link.remove(); });

      var new_links = [];
      _.each(parents, function (parent) { new_links.push(appRef.addLink(parent, cell.id))});

      graph.addCells(new_links);
      appRef.layout();
    }

    $('#updateDivision').modal('hide');
    return false;
  };

  // call the init method
  appRef.init();
}