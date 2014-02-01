needs = _.extend {}, celestrium.defs["DataProvider"].needs
needs["dimSlider"] = "DimSlider"
needs["graphView"] = "GraphView"

class AlarProvider extends celestrium.defs["DataProvider"]

  @uri: "AlarProvider"
  @needs: needs

  getLinks: (node, nodes, callback) ->
    $.ajax
      url: "kb/get_links"
      data:
        seed: @seed
        node: JSON.stringify node
        nodes: JSON.stringify nodes
      success: (links) =>
        _.each links, (link) =>
          @dimSlider.setStrength(link)
        callback(links)
      error: (e) ->
        console.log e.responseText

  getLinkedNodes: (nodes, callback) ->
    $.ajax
      url: "kb/get_similar_nodes"
      data:
        nodes: JSON.stringify nodes
        dimension: @dimSlider.dimModel.get("dimensionality")
      success: callback

celestrium.register AlarProvider

class KB

  @uri: "KB"
  @needs:
    "graphModel": "GraphModel"
    "dimSlider": "DimSlider"
    "graphView": "GraphView"
    "keyListener": "KeyListener"

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
            @graphModel.filterNodes (n) ->
              return n.type == node.type
            @graphModel.putNode(node)
          error: (e) ->
            console.log(e.responseText)
        $("#search").blur()

    # register seed button
    $("#btn-seed").click () =>
      @graphModel.filterNodes () -> false
      get_option = (id) ->
        val = $(id).val()
        if val.length is 0 then return null else return val
      seed =
        seedType: $("#seed-type").val()
        concept1: get_option("#concept1")
        relation: get_option("#relation")
        concept2: get_option("#concept2")
        dimension: 1
      $.ajax
        url: "kb/get_seed_nodes"
        data: {seed: JSON.stringify(seed)}
        success: (nodes) =>
          _.each nodes, (node) =>
            @graphModel.putNode node
        error: (e) ->
          console.log e.responseText
      $.ajax
        url: "kb/get_rank"
        success: (rank) ->
          @dimSlider.dimModel.set("max", rank)
          @dimSlider.dimModel.trigger("change:max")
    # format nodes
    @graphView.on "enter:node", () =>
      @renderNodes()
    @dimSlider.dimModel.on "change:dimensionality", (dim) =>
      @renderNodes()

  renderNodes: () ->
    dimSlider = @dimSlider
    @graphView.getNodeSelection().filter((d) =>
        return d.truth_coeffs?
    ).each((d) ->
      truth = dimSlider.interpolate(d.truth_coeffs)
      console.log d.text, truth
      d3.select(this).select("circle")
        .attr("r", Math.min(Math.max(1, 10*truth), 10))
        .attr("fill", if d.original then "black" else "green")
      d3.select(this).select("text")
        .attr("font-size", Math.min(Math.max(10, 15*truth), 15))
    )

celestrium.register KB

# finally do something

$ ->
  celestrium.init
    "KeyListener": {}
    "GraphModel": {}
    "GraphView": {}
    "Stats": {el: document.querySelector "#stats-cell"}
    "KB": {}
    "Sliders": {el: document.querySelector "#sliders"}
    "ForceSliders": {}
    "DimSlider": {}
    "LinkDistribution": {el: document.querySelector "#link-strength-histogram"}
    "AlarProvider": {}
    "NodeSelection": {}
