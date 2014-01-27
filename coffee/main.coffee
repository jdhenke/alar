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
        seed: @seed
        node: JSON.stringify nodes
        dimension: @dimSlider.dimModel.get("dimensionality")
      success: callback

celestrium.register AlarProvider

class KB

  @uri: "KB"
  @needs:
    "graphModel": "GraphModel"
    "dimSlider": "DimSlider"
    "graphView": "GraphView"

  constructor: () ->
    # sync off the bat
    @syncKB()
    # register save button
    $("#btn-save").click () =>
      assertionsText = $("#assertions").val()
      $.ajax
        url: "kb/new"
        data:
          assertionsText: assertionsText
        success: () =>
          @syncKB()
        error: (e) ->
          console.log e.responseText
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


  syncKB: () ->
    @graphModel.filterNodes () -> false
    $.ajax
      url: "kb/get_assertions"
      success: (assertionsText) ->
        $("#assertions").val(assertionsText)
      error: (e) ->
        console.log e.responseText
    $.ajax
      url: "kb/get_concepts"
      success: (concepts) ->
        $(".concept-input").typeahead
          local: concepts
    $.ajax
      url: "kb/get_relations"
      success: (relations) ->
        $(".relation-input").typeahead
          local: relations

  renderNodes: () ->
    dimSlider = @dimSlider
    @graphView.getNodeSelection().filter((d) =>
        return d.truth_coeffs?
    ).each((d) ->
      radius = dimSlider.interpolate(d.truth_coeffs)
      scale = d3.scale.linear()
        .domain([0.5,1])
        .range(1,30)
      d3.select(this).select("circle")
        .attr("r", 10 * radius)
        .attr("fill", if d.original then "green" else "red")
      return radius
    )

celestrium.register KB

# provides a variably smoothed PDF of the distribution link strengths.
# also provides a slider on that distribution
# which filters out links with weight below that threshold.

margin =
  top: 10
  right: 10
  bottom: 40
  left: 10

width = 200 - margin.left - margin.right
height = 200 - margin.top - margin.bottom
minStrength = 0
maxStrength = 1

class AssertionDistributionView extends Backbone.View

  @uri: "AssertionDistribution"
  @needs:
    graphModel: "GraphModel"
    graphView: "GraphView"
    sliders: "Sliders"

  className: "link-pdf"

  constructor: (@options) ->
    @windowModel = new Backbone.Model()
    @windowModel.set("window", 10)
    @listenTo @windowModel, "change:window", @paint
    super(@options)
    @listenTo @graphModel, "change:links", @paint
    scale = d3.scale.linear()
      .domain([2,200])
      .range([0, 100])
    @sliders.addSlider "Smoothing",
      scale(@windowModel.get("window")), (val) =>
        @windowModel.set "window", scale.invert(val)
    @render()

  render: ->

    ### one time setup of link strength pdf view ###

    # create cleanly transformed workspace to generate display
    @svg = d3.select(@el)
            .append("svg")
            .classed("pdf", true)
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .classed("workspace", true)
            .attr("transform", "translate(#{margin.left},#{margin.top})")
    @svg.append("g")
      .classed("pdfs", true)

    # scale mapping link strength to x coordinate in workspace
    @x = d3.scale.linear()
      .domain([minStrength, maxStrength])
      .range([0, width])

    # create axis
    xAxis = d3.svg.axis()
      .scale(@x)
      .orient("bottom")
    bottom = @svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0,#{height})")
    bottom.append("g")
      .call(xAxis)
    bottom.append("text")
      .classed("label", true)
      .attr("x", width / 2)
      .attr("y", 35)
      .text("Assertion Truths")

    # initialize plot
    @paint()

    ### create draggable threshold line ###

    # # create threshold line
    # d3.select(@el).select(".workspace")
    #   .append("line")
    #   .classed("threshold-line", true)

    # # x coordinate of threshold
    # thresholdX = @x(@graphView.getLinkFilter().get("threshold"))

    # # draw initial line
    # d3.select(@el).select(".threshold-line")
    #   .attr("x1", thresholdX)
    #   .attr("x2", thresholdX)
    #   .attr("y1", 0)
    #   .attr("y2", height)

    # # handling dragging
    # @$(".threshold-line").on "mousedown", (e) =>
    #   $line = @$(".threshold-line")
    #   pageX = e.pageX
    #   originalX = parseInt $line.attr("x1")
    #   d3.select(@el).classed("drag", true)
    #   $(window).one "mouseup", () =>
    #     $(window).off "mousemove", moveListener
    #     d3.select(@el).classed("drag", false)
    #   moveListener = (e) =>
    #     @paint()
    #     dx = e.pageX - pageX
    #     newX = Math.min(Math.max(0, originalX + dx), width)
    #     @graphView.getLinkFilter().set("threshold", @x.invert(newX))
    #     $line.attr("x1", newX)
    #     $line.attr("x2", newX)
    #   $(window).on "mousemove", moveListener
    #   e.preventDefault()

    # for chained calls
    return this

  paint: ->

    ### function called everytime link strengths change ###

    # use histogram layout with many bins to get discrete pdf
    layout = d3.layout.histogram()
      .range([minStrength, maxStrength])
      .frequency(false) # tells d3 to use probabilities, not counts
      .bins(100) # determines the granularity of the display

    # raw distribution of link strengths
    values = _.pluck @graphModel.getNodes(), "strength"
    # console.log values
    sum = 0
    cdf = _.chain(layout(values))
      .map (bin) ->
        "x": bin.x, "y": sum += bin.y
      .value()
    halfWindow = Math.max 1, parseInt(@windowModel.get("window")/2)
    pdf = _.map cdf, (bin, i) ->
      # get quantiles
      q1 = Math.max 0, i - halfWindow
      q2 = Math.min cdf.length - 1, i + halfWindow
      # get y value at quantiles
      y1 = cdf[q1]["y"]
      y2 = cdf[q2]["y"]
      # get slope
      slope = (y2 - y1) / (q2 - q1)
      # return slope as y to produce a smoothed derivative
      return "x": bin.x, "y": slope

    # scale mapping cdf to y coordinate in workspace
    maxY = _.chain(pdf)
      .map((bin) -> bin.y)
      .max()
      .value()
    @y = d3.scale.linear()
      .domain([0, maxY])
      .range([height, 0])

    # create area generator based on pdf
    area = d3.svg.area()
      .interpolate("monotone")
      .x((d) => @x(d.x))
      .y0(@y(0))
      .y1((d) => @y(d.y))

    ###

    define the x and y points to use for the visible links.
    they should be the points from the original pdf that are above
    the threshold

    to avoid granularity issues (jdhenke/celestrium#75),
    we also prepend this list of points with a point with x value exactly at
    the threshold and y value that is the average of it's neighbors' y values

    ###

    threshold = 0 # @graphView.getLinkFilter().get("threshold")
    visiblePDF = _.filter pdf, (bin) ->
      bin.x > threshold
    if visiblePDF.length > 0
      i = pdf.length - visiblePDF.length
      if i > 0
        y = (pdf[i-1].y + pdf[i].y) / 2.0
      else
        y = pdf[i].y
      visiblePDF.unshift
        "x": threshold
        "y": y

    # set opacity on area, bad I know
    pdf.opacity = 0.25
    visiblePDF.opacity = 1

    data = [pdf]
    data.push visiblePDF unless visiblePDF.length is 0

    path = d3
      .select(@el)
      .select(".pdfs")
      .selectAll(".pdf")
        .data(data)
    path.enter()
      .append("path")
      .classed("pdf", true)
    path.exit().remove()
    path
      .attr("d", area)
      .style("opacity", (d) -> d.opacity)

celestrium.register AssertionDistributionView

# finally do something

$ ->
  celestrium.init
    "KeyListener": {}
    "GraphModel": {}
    "GraphView": {}
    "Stats": {el: document.querySelector "#stats-cell"}
    "KB": {}
    "Sliders": {el: document.querySelector "#sliders-cell"}
    "ForceSliders": {}
    "DimSlider": {}
    "LinkDistribution": {el: document.querySelector "#link-histogram-cell"}
    "AssertionDistribution": {el: document.querySelector "#node-histogram-cell"}
    "AlarProvider": {}
    "NodeSelection": {}
