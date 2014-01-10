# interface to uap's semantic network
# nodes are concepts from a semantic network
# links are the relatedness of two concepts


# minStrength is the minimum similarity
# two nodes must have to be considered linked.
# this is evaluated at the minimum dimensionality
numNodes = 25

needs = _.extend {}, celestrium.defs["DataProvider"].needs
needs["dimSlider"] = "DimSlider"

class AssertionProvider extends celestrium.defs["DataProvider"]

  @uri: "AssertionProvider"
  @needs: needs

  getLinks: (node, nodes, callback) ->
    data =
      node: JSON.stringify(node)
      otherNodes: JSON.stringify(nodes)
    @ajax "kb/get_links", data, (arrayOfCoeffs) ->
      callback _.map arrayOfCoeffs, (coeffs, i) ->
        coeffs: coeffs

  getLinkedNodes: (nodes, callback) ->
    data =
      nodes: JSON.stringify(nodes)
      numNodes: numNodes
    @ajax "kb/get_linked_nodes", data, callback

  # initialize each link's strength before being added to the graph model
  linkFilter: (link) ->
    @dimSlider.setLinkStrength(link)
    return true

celestrium.register AssertionProvider
