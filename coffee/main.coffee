needs = _.extend {}, celestrium.defs["DataProvider"].needs
needs["dimSlider"] = "DimSlider"
needs["graphView"] = "GraphView"

class CustomProvider extends celestrium.defs["DataProvider"]

  @uri: "CustomProvider"
  @needs: needs

  constructor: (@seed) ->
    super()
    $.ajax
      url: "kb/get_seed_nodes"
      data:
        seed: JSON.stringify @seed
      success: (nodes) =>
        _.each nodes, (node) =>
          @graphModel.putNode(node)
      error: (e) ->
        console.log e.responseText
    @graphView.on "enter:node", () =>
      @renderNodes()
    @dimSlider.dimModel.on "change:dimensionality", (dim) =>
      @renderNodes()

  renderNodes: () ->
    dimSlider = @dimSlider
    @graphView.getNodeSelection().filter((d) =>
        return d.truth_coeffs?
    ).each((d) ->
      radius = dimSlider.interpolate(d.truth_coeffs)
      scale = d3.scale.linear()
        .domain([0.5,1])
        .range(1,30)
      d3.select(this).select("circle").attr("r", 10 * radius)
      return radius
    )

  getLinks: (node, nodes, callback) ->
    $.ajax
      url: "kb/get_links"
      data:
        seed: @seed
        node: JSON.stringify node
        nodes: JSON.stringify nodes
      success: (links) =>
        _.each links, (link) =>
          @dimSlider.setLinkStrength(link)
        callback(links)
      error: (e) ->
        console.log e.responseText

  getLinkedNodes: (nodes, callback) ->
    $.ajax
      url: "kb/get_similar_nodes"
      data:
        seed: @seed
        node: JSON.stringify nodes
        dimension: @dimSlider.dimModel.get("dimensionality")
      success: callback

celestrium.register CustomProvider

createGraph = (seed) ->

  $.ajax
    url: "/kb/get_rank"
    success: (rank) ->

      seed["dimension"] = rank

      celestrium.init
        "Layout":
          "el": document.querySelector "#workspace"
          "title": "UAP"
        "KeyListener":
          document.querySelector "body"
        "GraphModel":
          "nodeHash": (node) -> node.text
          "linkHash": (link) -> link.source.text + link.target.text
        "GraphView": {}
        "Sliders": {}
        "ForceSliders": {}
        "Stats": {}
        "NodeSelection": {}
        "SelectionLayer": {}
        "LinkDistribution": {}
        "DimSlider": [0, rank]
        "CustomProvider": seed

initTypeahead = () ->

  # initialize concept inputs
  $.ajax
    url: "kb/get_concepts"
    success: (concepts) ->
      $(".concept-input").typeahead
        local: concepts

  # initialize relation inputs
  $.ajax
    url: "kb/get_relations"
    success: (relations) ->
      $(".relation-input").typeahead
        local: relations

registerExplore = () ->
  $("#btn-explore").click () ->
    get_option = (id) ->
      val = $(id).val()
      if val.length is 0 then return null else return val
    createGraph
      seedType: $("#seed-type").val()
      concept1: get_option("#concept1")
      relation: get_option("#relation")
      concept2: get_option("#concept2")

$ ->
  initTypeahead()
  registerExplore()
