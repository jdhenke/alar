import json, traceback
from pecan import expose, redirect, response
from webob.exc import status_map
from server.model import kb

num_nodes = 40

# helpful methods to go from standard tuple representation to
# dictionary form used for JSON responses

def to_concept_node(concept):
  return {
    "type": "concept",
    "name": concept,
    "text": concept,
  }

def to_assertion_node(a):
  c1, r, c2 = a
  return {
    "type": "assertion",
    "concept1": c1,
    "relation": r,
    "concept2": c2,
    "text": "%s %s %s" % (c1, r, c2, ),
    "truth_coeffs": list(kb.get_assertion_truth_coeffs((c1, r, c2))),
    "original": kb.is_original_assertion(tuple(a)),
  }

to_concept = lambda n: n["name"]
to_assertion = lambda n: (n["concept1"], n["relation"], n["concept2"],)

def get_similar_concept_nodes(concept, rank):
  return map(to_concept_node,
             kb.get_similar_concepts(concept, rank, num_nodes))

def get_similar_assertion_nodes(assertion, rank):
  return map(to_assertion_node,
             kb.get_similar_assertions(assertion, rank, num_nodes))

# functions which form links

def get_concept_links(node, nodes):
  get_sim_coeffs = kb.get_concept_similarity_coeffs
  return _get_links(node, nodes, to_concept, get_sim_coeffs)

def get_assertion_links(node, nodes):
  get_sim_coeffs = kb.get_assertion_similarity_coeffs
  return _get_links(node, nodes, to_assertion, get_sim_coeffs)

def _get_links(node, nodes, to_entity, get_sim_coeffs):
  e1 = to_entity(node)
  return map(lambda e2: {"truth_coeffs": list(get_sim_coeffs(e1, e2))},
             map(to_entity, nodes))

## actual controllers

class KBController(object):

  @expose('json')
  def get_node(self, text):
    components = text.lower().split()
    if len(components) == 1:
      return to_concept_node(text)
    elif len(components) == 2:
      return to_feature_node(text)
    elif len(components) == 3:
      return to_assertion_node(components)
    else:
      response.status = 400
      return "Couldn't parse to concept or assertion"

  @expose('json')
  def get_links(self, node, nodes):
    try:
      node = json.loads(node)
      nodes = json.loads(nodes)
      if node["type"] == "concept":
        return get_concept_links(node, nodes)
      elif node["type"] == "assertion":
        return get_assertion_links(node, nodes)
    except Exception as e:
      traceback.print_exc()
      response.status = 400
      return {"error": str(e)}

  @expose('json')
  def get_nodes(self, node, rank):
    try:
      rank = int(float(rank))
      node = json.loads(node)
      if node["type"] == "concept":
        concept = to_concept(node)
        return get_similar_concept_nodes(concept, rank)
      elif node["type"] == "assertion":
        assertion = to_assertion(node)
        return get_similar_assertion_nodes(assertion, rank)
    except Exception as e:
      traceback.print_exc()
      response.status = 400
      return {"error": str(e)}

  @expose('json')
  def get_rank(self):
    return kb.rank

class RootController(object):

  @expose(template="index.html")
  def index(self):
    return {}

  @expose('error.html')
  def error(self, status):
    try:
      status = int(status)
    except ValueError:  # pragma: no cover
      status = 500
    message = getattr(status_map.get(status), 'explanation', '')
    return dict(status=status, message=message)

  kb = KBController()
