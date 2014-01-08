# call with server's response to ping about dimensionality
main = (response) ->

  # initialize the workspace with all the below plugins
  celestrium.init
    # these come with celestrium
    # their arguments should be specific to this data set
    "Layout":
      "el": document.querySelector "body"
      "title": "UAP"
    "KeyListener":
      document.querySelector "body"
    "GraphModel":
      "nodeHash": (node) -> node.text
      "linkHash": (link) -> link.source.text + link.target.text
    "GraphView": {}
    "Sliders": {}
    "ForceSliders": {}
    # "NodeSearch":
    #   prefetch: "get_nodes"
    "Stats": {}
    "NodeSelection": {}
    "SelectionLayer": {}
    # "NodeDetails": {}
    "LinkDistribution": {}
    # these are plugins i defined specific to this data set
    "DimSlider":
      [response.min, response.max]
    # "uap/ConceptProvider": {}
    "AssertionProvider": {}
    "AssertionSearch":
      conceptPrefetch: "/get_concepts"
      relationPrefetch: "/get_relations"

$ ->
  $.ajax
    url: "get_dimensionality_bounds"
    success: main
