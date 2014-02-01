import json, traceback
from server.model import kb, create_kb_from_text
from pecan import expose, redirect, response
from webob.exc import status_map

# functions which form lists of nodes with specific criteria

num_nodes = 20

# similarity criteria a.k.a. things similar to seed

def get_similar_concept_nodes(concept, dimension):
  print concept, dimension
  concepts = kb.get_similar_concepts(concept, dimension, num_nodes)
  return [to_concept_node(c) for c in concepts]

def get_similar_feature_nodes(feature, dimension):
  features = kb.get_similar_features(feature, dimension, num_nodes)
  return [to_feature_node(f) for f in features]

def get_similar_assertion_nodes(assertion, dimension):
  assertions = kb.get_similar_assertions(assertion, dimension, num_nodes)
  return [to_assertion_node(a) for a in assertions]

# complimentary criteria a.k.a. fill in the blanks for seed.
# the major difference here is that they represent assertions
# so represent a valid statement which has a truth that
# varies across dimensions

def get_complimentary_features(concept, dimension):
  features = kb.get_top_features(concept, dimension, num_nodes)
  nodes = []
  for feature in features:
    d, r, c = feature
    a = (concept, r, c) if d == 'right' else (c, r, concept)
    node = to_feature_node(feature)
    node["truth_coeffs"] = list(kb.get_assertion_truth_coeffs(a))
    node["original"] = kb.is_original_assertion(a)
    nodes.append(node)
  return nodes

def get_complimentary_concepts(feature, dimension):
  concepts = kb.get_top_concepts(feature, dimension, num_nodes)
  nodes = []
  d, r, c = feature
  for concept in concepts:
    a = (concept, r, c) if d == 'right' else (c, r, concept)
    node = to_concept_node(concept)
    node["truth_coeffs"] = list(kb.get_assertion_truth_coeffs(a))
    node["original"] = kb.is_original_assertion(a)
    nodes.append(node)
  return nodes

# helpful methods to go from standard tuple representation to
# dictionary form used for JSON responses

def to_concept_node(concept):
  return {
    "type": "concept",
    "name": concept,
    "text": concept,
  }

def to_feature_node(f):
  direction, relation, concept = f
  return {
    "type": "feature",
    "direction":  direction,
    "relation": relation,
    "concept": concept,
    "text": "%s,%s,%s" % ("_", relation, concept) if direction == 'right' else\
      (concept, relation, "_"),
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
    "original": kb.is_original_assertion(a),
  }

# helpful methods to go from dictionary representation to standard tuples

to_concept = lambda n: n["name"]
to_feature = lambda n: (n["direction"], n["relation"], n["concept"],)
to_assertion = lambda n: (n["concept1"], n["relation"], n["concept2"],)

# functions which form links

def get_concept_links(node, nodes):
  get_sim_coeffs = kb.get_concept_similarity_coeffs
  return _get_links(node, nodes, to_concept, get_sim_coeffs)

def get_feature_links(node, nodes):
  get_sim_coeffs = kb.get_feature_similarity_coeffs
  return _get_links(node, nodes, to_feature, get_sim_coeffs)

def get_assertion_links(node, nodes):
  get_sim_coeffs = kb.get_assertion_similarity_coeffs
  return _get_links(node, nodes, to_assertion, get_sim_coeffs)

def _get_links(node, nodes, to_entity, get_sim_coeffs):
  links = []
  e1 = to_entity(node)
  for n in nodes:
    e2 = to_entity(n)
    links.append({
      "truth_coeffs": list(get_sim_coeffs(e1, e2)),
    })
  return links

class KBController(object):

  @expose('json')
  def new(self, assertionsText):
    global kb
    try:
      kb = create_kb_from_text(assertionsText)
    except Exception as e:
      response.status = 400
      return {"error": str(e)}

  @expose('json')
  def get_node(self, text):
    components = text.split()
    if len(components) == 1:
      return to_concept_node(text)
    elif len(components) == 3:
      return to_assertion_node(components)
    else:
      response.status = 400
      return "Couldn't parse to concept or assertion"

  @expose('json')
  def get_rank(self):
    return kb.get_rank() - 1

  @expose('json')
  def get_concepts(self):
    return list(kb.get_concepts())

  @expose('json')
  def get_relations(self):
    return list(kb.get_relations())

  @expose('json')
  def get_assertions(self):
    return "\n".join([("%s %s %s" % tuple(a)) for a in kb.get_assertions()])

  @expose('json')
  def get_rank(self):
    return kb.get_rank()

  @expose('json')
  def get_seed_nodes(self, seed):
    seed = json.loads(seed)
    try:
      seed_type = seed["seedType"]
      c1 = seed["concept1"]
      r = seed["relation"]
      c2 = seed["concept2"]
      d = int(seed["dimension"])
      if seed_type == 'similar':
        if c1 and not r and not c2:
          # similar to c1
          return get_similar_concept_nodes(c1, d)
        elif c2 and not r and not c1:
          # similar to c2
          return get_similar_concept_nodes(c2, d)
        elif c1 and r and not c2:
          # similar to left feature
          return get_similar_feature_nodes(('left', r, c1), d)
        elif c2 and r and not c1:
          # similar to right feature
          return get_similar_feature_nodes(('right', r, c2), d)
        elif c1 and c2 and r:
          # similar to assertions
          return get_similar_assertion_nodes((c1, r, c2), d)
      elif seed_type == 'compliment':
        if c1 and not r and not c2:
          # feature which compliments c1
          return get_complimentary_features(c1, d)
        elif c2 and not r and not c1:
          # compliment c2
          return get_complimentary_features(c2, d)
        elif c1 and r and not c2:
          # compliment left feature
          return get_complimentary_concepts(('left', r, c1), d)
        elif c2 and r and not c1:
          # compliment right feature
          return get_complimentary_concepts(('right', r, c2), d)
      raise Exception("can't handle that seed: %s" % (seed, ))
    except Exception as e:
      traceback.print_exc()
      response.status = 400
      return {"error": str(e)}

  @expose('json')
  def get_links(self, node, nodes):
    try:
      node = json.loads(node)
      nodes = json.loads(nodes)
      if node["type"] == "concept":
        return get_concept_links(node, nodes)
      elif node["type"] == "feature":
        return get_feature_links(node, nodes)
      elif node["type"] == "assertion":
        return get_assertion_links(node, nodes)
    except Exception as e:
      response.status = 400
      return {"error": str(e)}
    # response.status = 400
    # return {"error": "unknown node type for node %s" % (node, )}

  @expose('json')
  def get_similar_nodes(self, nodes, dimension):
    dimension = int(float(dimension))
    try:
      nodes = json.loads(nodes)
      output = []
      for node in nodes:
        if node["type"] == "concept":
          concept = to_concept(node)
          output.extend(get_similar_concept_nodes(concept, dimension))
        elif node["type"] == "feature":
          feature = to_feature(node)
          output.extend(get_similar_feature_nodes(feature, dimension))
        elif node["type"] == "assertion":
          assertion = to_assertion(node)
          output.extend(get_similar_assertion_nodes(assertion, dimension))
      return output
    except Exception as e:
      traceback.print_exc()
      response.status = 400
      return {"error": str(e)}

class RootController(object):

  @expose(template="index.html")
  def index(self):
    return {
      "num_assertions": kb.get_num_assertions(),
      "num_concepts":  kb.get_num_concepts(),
      "num_features": kb.get_num_features(),
    }

  @expose()
  def add(self, assertions):
    redirect('/')

  @expose(template='explore.html')
  def explore(self):
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
