needs = _.extend {}, celestrium.defs["DataSource"].needs
needs["rankSlider"] = "RankSlider"
needs["graph"] = "Graph"

class AlarProvider extends celestrium.defs["DataSource"]

  @uri: "AlarProvider"
  @needs: needs

  cleanNode: (node) -> _.pick node, "name", "type", "concept1", "relation", "concept2", "concept", "direction"

  addNodes: (node, callback) ->
    $.ajax
      url: "/kb/get_nodes"
      data:
        node: JSON.stringify(@cleanNode(node))
        rank: @rankSlider.get("rank")
      success: callback
  addLinks: (node, callback) ->
    $.ajax
      url: "/kb/get_links"
      data:
        node: JSON.stringify @cleanNode(node)
        nodes: JSON.stringify _.map(@graph.nodes, @cleanNode)
      type: "POST"
      success: callback
  searchAround: (node) ->
    @addNodes node, (nodes) =>
      _.each nodes, (node) =>
        present = _.some @graph.nodes, (currentNode) ->
          node.text == currentNode.text
        if not present
          @graph.nodes.push(node)

celestrium.register AlarProvider

class RankSlider extends Backbone.Model

  @uri: "RankSlider"
  @needs:
    "graph": "Graph"
    "sliders": "Sliders"

  constructor: (max) ->

    max -= 1

    # ensure backbone model components are initialized
    super()

    paintNodes = () =>
      s = @graph.getNodeSelection().filter (d) -> d.truth_coeffs?
      s.select("circle")
        .attr "r", (d) =>
          return Math.max(2, Math.min(10, d.strength * 20))
        .attr("fill", (d) -> if d.original then "black" else "green")

    @graph.on "enter:node", paintNodes

    # update link strengths when the rank changes
    @on "change:rank", () =>
      _.each @graph.links, (link) =>
        @setStrength link
      _.each @graph.nodes, (node) =>
        @setStrength node
      @graph.links.trigger "change", this
      @graph.nodes.trigger "change", this
      paintNodes()
      @graph.force.start()


    @set "rank", max

    @listenTo @graph.links, "add", (link) =>
      @setStrength link
    @listenTo @graph.nodes, "add", (node) =>
      @setStrength node

    # add rank slider into ui
    # create scale to map rank to slider value in ui
    scale = d3.scale.linear()
      .domain([0, max])
      .range([0, 100])
    that = this
    @sliders.addSlider "Rank", scale(@get("rank")), (val) ->
      that.set "rank", scale.invert val
      $(this).blur()

  # set link.strength based on its coefficients and
  # the current rank
  setStrength: (obj) ->
    if obj.truth_coeffs
      obj.strength = @interpolate(obj.truth_coeffs)

  # reconstruct polynomial from coefficients
  # from least squares polynomial fit done server side,
  # and return that polynomial evaluated
  # at the current rank
  interpolate: (coeffs) ->
    degree = coeffs.length
    strength = 0
    rank = @get("rank")
    dimMultiple = 1
    i = coeffs.length
    while i > 0
      i -= 1
      strength += coeffs[i] * dimMultiple
      dimMultiple *= rank
    return Math.max(0, Math.min(strength, 1))

celestrium.register RankSlider

class KB

  @uri: "KB"
  @needs:
    "graph": "Graph"
    "rankSlider": "RankSlider"
    "keyListener": "KeyListener"
    "alarProvider": "AlarProvider"

  constructor: (data) ->
    @concepts = data.concepts
    @relations = data.relations
    @keyListener.on "down:191", (e) ->
      e.preventDefault()
      $("#search").focus()
    # register search button
    # $("#search").keyup (e) =>
    #   if e.which == 13
    #     $.ajax
    #       url: "kb/get_node"
    #       data:
    #         "text": $("#search").val()
    #       success: (node) =>
    #         @graph.nodes.clear()
    #         @graph.links.clear()
    #         node.x = $(window).width() / 2
    #         node.y = $(window).height() / 2
    #         node.fixed = true
    #         @graph.nodes.push node
    #         @graph.getNodeSelection()
    #           .classed("centered", (n) -> "centered" if n is node)
    #         @alarProvider.searchAround(node)
    #       error: (e) ->
    #         console.log(e.responseText)
    #     $("#search").blur()

    $("#search").typeahead {
        displayKey: 'value',
      },
      name: "kb"
      source: (query, cb) =>
        terms = query.split(/\s+/)
        last_term = terms[terms.length - 1]
        if terms.length == 1
          cb _.chain([@concepts, @relations]).flatten().filter((c) ->
              c.indexOf(last_term) == 0
            ).map((c) ->
              value: c
            ).value()
        else if terms.length == 2
          if @relations.indexOf(terms[0]) >= 0
            cb _.chain(@concepts).filter((c) ->
                last_term.length > 0 && c.indexOf(last_term) == 0
              ).map((c) ->
                value: terms[0] + " " + c
              ).value()
          else if @concepts.indexOf(terms[0]) >= 0
            cb _.chain(@relations).filter((r) ->
                last_term.length > 0 && r.indexOf(last_term) == 0
              ).map((r) ->
                value: terms[0] + " " + r
              ).value()
          else cb []
        else
          if @concepts.indexOf(terms[0]) >= 0 && @relations.indexOf(terms[1]) >= 0
            cb _.chain(@concepts).filter((c) ->
                last_term.length > 0 && c.indexOf(last_term) == 0
              ).map((c) ->
                value: terms[0] + " " + terms[1] + " " + c
              ).value()
          else
            cb []

    .on("typeahead:selected", (evt, obj) =>
      $.ajax
        url: "kb/get_node"
        data:
          "text": obj.value
        success: (node) =>
          @graph.nodes.clear()
          @graph.links.clear()
          node.x = $(window).width() / 2
          node.y = $(window).height() / 2
          node.fixed = true
          @graph.nodes.push node
          @graph.getNodeSelection()
            .classed("centered", (n) -> "centered" if n is node)
          @alarProvider.searchAround(node)
        error: (e) ->
          console.log(e.responseText)
    )

celestrium.register KB

# finally do something

$ ->
  $.ajax
    url: "kb/init"
    success: (opts) ->
      celestrium.init
        "KeyListener": {}
        "Graph": {el: document.querySelector "#graph"}
        "KB":
          concepts: opts.concepts
          relations: opts.relations
        "Sliders": {el: document.querySelector "#sliders"}
        "ForceSliders": {}
        "RankSlider": opts.rank
        "LinkDistro": {el: document.querySelector "#link-strength-histogram"}
        "AlarProvider": {}
