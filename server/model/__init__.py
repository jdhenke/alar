import divisi2
from divisi2.sparse import SparseMatrix
from divisi2 import OrderedSet
from pysparse.sparse import PysparseMatrix

# TODO:
#  - normalization?
#  - handle left vs. right when given assertion
#    - when forming matrix
#    - when truth value is requested
#  - assertion similarities

def create_sparse_matrix(assertions):

  # collections to be built up when iterating through the assertions
  weights, row_indices, col_indices = [], [], []
  concepts, features  = OrderedSet(), OrderedSet()

  # do a single pass over the assertions
  for assertion in assertions:

    # parse out components of assertion
    c1, r, c2 = assertion[:3]
    f1, f2 = ('right', r, c2), ('left', r, c1)
    weight = float(assertion[3]) if len(assertion) > 3 else 1.0

    # add to orderedsets and get indices
    concepts.extend([c1, c2])
    features.extend([f1, f2])
    ic1, ic2 = concepts.index(c1), concepts.index(c2)
    if1, if2 = features.index(f1), features.index(f2)

    # add indicies and weights
    row_indices.extend((ic1, ic2))
    col_indices.extend((if1, if2))
    weights.extend((weight, weight))

  # create underlying pysparsematrix with accrued weights and indices
  data = PysparseMatrix(nrow=len(concepts), ncol=len(features))
  data.put(weights, row_indices, col_indices)

  # retun a nicely labeled sparse matrix
  return SparseMatrix(data, row_labels=concepts, col_labels=features)

# ADT of the notion of a knowledgebase
class Knowledgebase(object):

  def __init__(self, matrix, rank=100):
    # save original args
    self.matrix = matrix
    self.rank = rank

    # cache set of relations
    self.relations = set()
    for direction, relation, concept in matrix.col_labels:
      self.relations.add(relation)

    # cache results of SVD at maximum rank
    self.u, self.s, self.v = matrix.svd(k=rank)

  # O(1) size features

  def get_num_assertions(self):
    return self.matrix.nnz

  def get_num_concepts(self):
    return self.matrix.shape[0]

  def get_num_features(self):
    return self.matrix.shape[1]

  def get_rank(self):
    return self.rank

  # O(n) list accessors, mostly needed for typeahead

  def get_concepts(self):
    return self.matrix.row_labels

  def get_features(self):
    return self.matrix.col_labels

  def get_relations(self):
    return self.relations

  # get contribution of each dimension to the following

  def get_assertion_truth_delta(self, i, j, d):
    return self.u[i][d] * self.s[d] * self.v[j][d]

  def get_concept_similarity_delta(self, i, j, d):
    return self.u[i][d] * (self.s[d] ** 2) * self.u[j][d]

  def get_feature_similarity_delta(self, i, j, d):
    return self.v[i][d] * (self.s[d] ** 2) * self.v[j][d]

  # get value of single cell as if SVD was computed at rank=k

  def get_assertion_truth(self, a, k):
    c1, r, c2 = a
    feature = ('right', r, c2)
    i = self.u.row_index(c1)
    j = self.v.row_index(feature)
    return sum([self.get_assertion_truth_delta(i, j, d) for d in xrange(k)])

  def get_concept_similarity(self, c1, c2, k):
    i = self.u.row_index(c1)
    j = self.u.row_index(c2)
    return sum([self.get_concept_similarity_delta(i, j, d) for d in xrange(k)])

  def get_feature_similarity(self, f1, f2, k):
    i = self.v.row_index(f1)
    j = self.v.row_index(f2)
    return sum([self.get_feature_similarity_delta(i, j, d) for d in xrange(k)])

  # use value of row as if SVD was computed at rank=k

  def get_similar_concepts(self, c, k, n):
    concepts = self.get_concepts()
    get_sim = lambda c2: self.get_concept_similarity(c, c2, k)
    items = sorted([(get_sim(c2), c2) for c2 in concepts], reverse=True)[:n]
    return [b for a, b in items]

  def get_similar_features(self, f, k, n):
    features = self.get_features()
    get_sim = lambda f2: self.get_feature_similarity(f, f2, k)
    items = sorted([(get_sim(f2), f2) for f2 in features], reverse=True)[:n]
    return [b for a, b in items]

  # returns list of answer to question at each dimension

  def get_assertion_truth_history(self, a):
    c1, r, c2 = a
    feature = ('right', r, c2)
    i = self.u.row_index(c1)
    j = self.v.row_index(feature)
    get_delta = lambda d: self.get_assertion_truth_delta(i, j, d)
    return self._get_history(get_delta)

  def get_concept_similarity_history(self, c1, c2):
    i = self.u.row_index(c1)
    j = self.u.row_index(c2)
    get_delta = lambda d: self.get_concept_similarity_delta(i, j, d)
    return self._get_history(get_delta)

  def get_feature_similarity_history(self, f1, f2):
    i = self.v.row_index(f1)
    j = self.v.row_index(f2)
    get_delta = lambda d: self.get_feature_similarity_delta(i, j, d)
    return self._get_history(get_delta)

  # helper function to accrue cumulative sum of deltas

  def _get_history(self, get_delta):
    total = 0
    history = []
    for d in xrange(self.rank):
      total += get_delta(d)
      history.append(total)
    return history

# global current instance of the knowledgebase
kb = None

def init_model():
  global kb
  # c4 = divisi2.network.conceptnet_matrix('en').normalize_all()
  # kb = Knowledgebase(c4, 100)
  m = create_sparse_matrix([["a", "r", "x"], ["a", "r", "y", 20], ["b", "r", "x", 5]])
  kb = Knowledgebase(m, 4)
  print kb.s
