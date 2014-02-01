class DimSlider extends Backbone.Model

  @uri: "DimSlider"
  @needs:
    "stats": "Stats"
    "graphModel": "GraphModel"
    "sliders": "Sliders"

  constructor: () ->

    [@min, @max] = [1, 99]

    # ensure backbone model components are initialized
    super()

    # create internal state to maintain current dimensionality
    @dimModel = new Backbone.Model({})
    @dimModel.set "min", @min
    @dimModel.set "max", @max
    @dimModel.set "dimensionality", @max

    # create stat view
    @updateDimStatUI = @stats.addStat("Dimensionality")
    updateDimStat = () =>
      @updateDimStatUI(parseInt(@dimModel.get("dimensionality")))
    updateDimStat()

    # update link strengths when the dimensionality changes
    @listenTo @dimModel, "change:dimensionality", () =>
      _.each @graphModel.getLinks(), @setStrength, this
      _.each @graphModel.getNodes(), @setStrength, this
      @graphModel.trigger "change:links"
      @graphModel.trigger "change:nodes"
      @graphModel.trigger "change"
      updateDimStat()

    @listenTo @graphModel, "add:node", @setStrength
    @listenTo @dimModel, "add:link", @setStrength

    # create scale to map dimensionality to slider value in ui
    scale = d3.scale.linear()
      .domain([@min, @max])
      .range([0, 100])

    # add dimensionality slider into ui
    dimModel = @dimModel
    @sliders.addSlider "Dimensionality", scale(@dimModel.get("dimensionality")), (val) ->
      dimModel.set "dimensionality", scale.invert val
      $(this).blur()

  # set link.strength based on its coefficients and
  # the current dimensionality
  setStrength: (obj) ->
    if obj.truth_coeffs
      obj.strength = @interpolate(obj.truth_coeffs)

  # reconstruct polynomial from coefficients
  # from least squares polynomial fit done server side,
  # and return that polynomial evaluated
  # at the current dimensionality
  interpolate: (coeffs) ->
    degree = coeffs.length
    strength = 0
    dimensionality = @dimModel.get("dimensionality")
    dimMultiple = 1
    i = coeffs.length
    while i > 0
      i -= 1
      strength += coeffs[i] * dimMultiple
      dimMultiple *= dimensionality
    return Math.min(strength, 1)

  updateRank: (rank) ->

celestrium.register DimSlider
