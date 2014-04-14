needs = _.extend {}, celestrium.defs["DataSource"].needs
needs["rankSlider"] = "RankSlider"
needs["graph"] = "Graph"

class AlarProvider extends celestrium.defs["DataSource"]

  @uri: "AlarProvider"
  @needs: needs

  searchAround: (node, callback) ->
    cleanNode = (node) -> _.pick node, "text"
    $.ajax
      url: "/kb/search_around"
      data:
        node: JSON.stringify cleanNode(node)
        nodes: JSON.stringify _.map(@graph.nodes, cleanNode)
        rank: @rankSlider.get("rank")
      type: "POST"

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

    # create internal state to maintain current rank
    @set "rank", max

    # update link strengths when the rank changes
    @on "change:rank", () =>
      _.each @graph.links, @setStrength, this
      _.each @graph.nodes, @setStrength, this
      @graph.links.trigger "change", this
      @graph.nodes.trigger "change", this

    @listenTo @graph.links, "change", (caller) =>
      if caller is not this
        _.each @graph.links, @setStrength, this
        _.each @graph.nodes, @setStrength, this

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
    return Math.min(strength, 1)

  updateRank: (rank) ->

celestrium.register RankSlider

class KB

  @uri: "KB"
  @needs:
    "graph": "Graph"
    "rankSlider": "RankSlider"
    "keyListener": "KeyListener"
    "alarProvider": "AlarProvider"

  constructor: () ->
    @keyListener.on "down:191", (e) ->
      e.preventDefault()
      $("#search").focus()
    # register search button
    $("#search").keyup (e) =>
      if e.which == 13
        $.ajax
          url: "kb/get_node"
          data:
            "text": $("#search").val()
          success: (node) =>
            @graph.nodes.clear()
            node.x = $(window).width() / 2
            node.y = $(window).height() / 2
            node.fixed = true
            @graph.nodes.push node
            @alarProvider.searchAround node, (nodes, links) =>
              _.each nodes, (node) =>
                @graph.nodes.push node
              _.each links, (link) =>
                @graph.links.push link
            @graph.getNodeSelection()
              .classed("centered", (n) -> "centered" if n is node)
          error: (e) ->
            console.log(e.responseText)
        $("#search").blur()

    # format nodes
    @graph.on "enter:node", () =>
      @renderNodes()
    @rankSlider.on "change:rank", (dim) =>
      @renderNodes()

  renderNodes: () ->
    rankSlider = @rankSlider
    @graph.getNodeSelection().filter((d) =>
        return d.truth_coeffs?
    ).each((d) ->
      truth = rankSlider.interpolate(d.truth_coeffs)
      d3.select(this).select("circle")
        .attr("r", Math.min(Math.max(1, 10*truth), 10))
        .attr("fill", if d.original then "black" else "green")
      d3.select(this).select("text")
        .attr("font-size", Math.min(Math.max(10, 15*truth), 15))
    )

celestrium.register KB

# finally do something

$ ->
  $.ajax
    url: "kb/get_rank"
    success: (rank) ->
      celestrium.init
        "KeyListener": {}
        "Graph": {el: document.querySelector "#graph"}
        "KB": {}
        "Sliders": {el: document.querySelector "#sliders"}
        "ForceSliders": {}
        "RankSlider": rank
        "LinkDistro": {el: document.querySelector "#link-strength-histogram"}
        "AlarProvider": {}
