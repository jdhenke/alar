(function() {
  var AssertionProvider, needs, numNodes, _ref,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  numNodes = 25;

  needs = _.extend({}, celestrium.defs["DataProvider"].needs);

  needs["dimSlider"] = "DimSlider";

  AssertionProvider = (function(_super) {
    __extends(AssertionProvider, _super);

    function AssertionProvider() {
      _ref = AssertionProvider.__super__.constructor.apply(this, arguments);
      return _ref;
    }

    AssertionProvider.uri = "AssertionProvider";

    AssertionProvider.needs = needs;

    AssertionProvider.prototype.getLinks = function(node, nodes, callback) {
      var data;
      data = {
        node: JSON.stringify(node),
        otherNodes: JSON.stringify(nodes)
      };
      return this.ajax("kb/get_links", data, function(arrayOfCoeffs) {
        return callback(_.map(arrayOfCoeffs, function(coeffs, i) {
          return {
            coeffs: coeffs
          };
        }));
      });
    };

    AssertionProvider.prototype.getLinkedNodes = function(nodes, callback) {
      var data;
      data = {
        nodes: JSON.stringify(nodes),
        numNodes: numNodes
      };
      return this.ajax("kb/get_linked_nodes", data, callback);
    };

    AssertionProvider.prototype.linkFilter = function(link) {
      this.dimSlider.setLinkStrength(link);
      return true;
    };

    return AssertionProvider;

  })(celestrium.defs["DataProvider"]);

  celestrium.register(AssertionProvider);

}).call(this);

(function() {
  var AssertionSearchView,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  AssertionSearchView = (function(_super) {
    __extends(AssertionSearchView, _super);

    AssertionSearchView.uri = "AssertionSearch";

    AssertionSearchView.needs = {
      graphView: "GraphView",
      dimSlider: "DimSlider",
      layout: "Layout",
      graphModel: "GraphModel"
    };

    AssertionSearchView.prototype.events = {
      "click #btn-add": "addAssertion"
    };

    function AssertionSearchView(options) {
      var colorScale, update,
        _this = this;
      this.options = options;
      AssertionSearchView.__super__.constructor.call(this);
      colorScale = d3.scale.linear().domain([0, 1]).range(["red", "green"]);
      update = function(n) {
        return colorScale(_this.dimSlider.interpolate(n.truth_coeffs));
      };
      this.graphView.on("enter:node", function(nodeSelection) {
        return nodeSelection.attr("fill", update);
      });
      this.dimSlider.dimModel.on("change:dimensionality", function() {
        return _this.graphView.getNodeSelection().attr("fill", update);
      });
      this.render();
      this.layout.addPlugin(this.el, "Search");
    }

    AssertionSearchView.prototype.render = function() {
      var button, conceptInput1, conceptInput2, container, input, inputContainer, relationInput, _i, _len, _ref,
        _this = this;
      container = $("<div />").addClass("node-search-container");
      conceptInput1 = $("<input type=\"text\" placeHolder=\"Concept 1...\" id=\"concept1\" />");
      relationInput = $("<input type=\"text\" placeHolder=\"Relation...\" id=\"relation\" />");
      conceptInput2 = $("<input type=\"text\" placeHolder=\"Concept 2...\" id=\"concept2\" />");
      inputContainer = $("<span />");
      _ref = [conceptInput1, relationInput, conceptInput2];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        input = _ref[_i];
        inputContainer.append($("<div />").append(input));
      }
      button = $("<button id=\"btn-add\">Add</button>");
      this.$el.append(container);
      container.append(inputContainer).append(button);
      _.each([conceptInput1, conceptInput2], function(conceptInput) {
        return conceptInput.typeahead({
          prefetch: _this.options.conceptPrefetch,
          name: "concepts",
          limit: 100,
          ttl: 10
        });
      });
      return relationInput.typeahead({
        prefetch: this.options.relationPrefetch,
        name: "relations"
      });
    };

    AssertionSearchView.prototype.addAssertion = function() {
      var concept1, concept2, node, relation, text,
        _this = this;
      concept1 = this.$("#concept1").val();
      concept2 = this.$("#concept2").val();
      relation = this.$("#relation").val();
      text = concept1 + " " + relation + " " + concept2;
      node = {
        concept1: concept1,
        concept2: concept2,
        relation: relation,
        text: text
      };
      return $.ajax({
        url: "kb/get_truth",
        data: {
          node: JSON.stringify(node)
        },
        success: function(response) {
          var newNode;
          newNode = _.extend(node, response);
          return _this.graphModel.putNode(newNode);
        }
      });
    };

    return AssertionSearchView;

  })(Backbone.View);

  celestrium.register(AssertionSearchView);

}).call(this);

(function() {
  var DimSlider,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  DimSlider = (function(_super) {
    __extends(DimSlider, _super);

    DimSlider.uri = "DimSlider";

    DimSlider.needs = {
      "stats": "Stats",
      "graphModel": "GraphModel",
      "sliders": "Sliders"
    };

    function DimSlider(options) {
      var dimModel, scale, updateDimStat,
        _this = this;
      this.min = options[0], this.max = options[1];
      DimSlider.__super__.constructor.call(this);
      this.dimModel = new Backbone.Model({});
      this.dimModel.set("min", this.min);
      this.dimModel.set("max", this.max);
      this.dimModel.set("dimensionality", this.max);
      this.updateDimStatUI = this.stats.addStat("Dimensionality");
      updateDimStat = function() {
        return _this.updateDimStatUI(parseInt(_this.dimModel.get("dimensionality")));
      };
      updateDimStat();
      this.listenTo(this.dimModel, "change:dimensionality", function() {
        _.each(_this.graphModel.getLinks(), _this.setLinkStrength, _this);
        _this.graphModel.trigger("change:links");
        _this.graphModel.trigger("change");
        return updateDimStat();
      });
      scale = d3.scale.linear().domain([this.min, this.max]).range([0, 100]);
      dimModel = this.dimModel;
      this.sliders.addSlider("Dimensionality", scale(this.dimModel.get("dimensionality")), function(val) {
        dimModel.set("dimensionality", scale.invert(val));
        return $(this).blur();
      });
    }

    DimSlider.prototype.setLinkStrength = function(link) {
      return link.strength = this.interpolate(link.coeffs);
    };

    DimSlider.prototype.interpolate = function(coeffs) {
      var degree, dimMultiple, dimensionality, i, strength;
      degree = coeffs.length;
      strength = 0;
      dimensionality = this.dimModel.get("dimensionality");
      dimMultiple = 1;
      i = coeffs.length;
      while (i > 0) {
        i -= 1;
        strength += coeffs[i] * dimMultiple;
        dimMultiple *= dimensionality;
      }
      return Math.min(1, Math.max(0, strength));
    };

    return DimSlider;

  })(Backbone.Model);

  celestrium.register(DimSlider);

}).call(this);

(function() {
  var main;

  main = function(response) {
    return celestrium.init({
      "Layout": {
        "el": document.querySelector("body"),
        "title": "UAP"
      },
      "KeyListener": document.querySelector("body"),
      "GraphModel": {
        "nodeHash": function(node) {
          return node.text;
        },
        "linkHash": function(link) {
          return link.source.text + link.target.text;
        }
      },
      "GraphView": {},
      "Sliders": {},
      "ForceSliders": {},
      "Stats": {},
      "NodeSelection": {},
      "SelectionLayer": {},
      "LinkDistribution": {},
      "DimSlider": [response.min, response.max],
      "AssertionProvider": {},
      "AssertionSearch": {
        conceptPrefetch: "/kb/get_concepts",
        relationPrefetch: "/kb/get_relations"
      }
    });
  };

  $(function() {
    return $.ajax({
      url: "kb/get_dimensionality_bounds",
      success: main
    });
  });

}).call(this);
