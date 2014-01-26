import divisi2, numpy
from divisi2 import OrderedSet
from divisi2.sparse import SparseMatrix
from divisi2.reconstructed import ReconstructedMatrix
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

  '''
  Only requirement is the matrix. Normalize it beforehand if you wish.

  Optional keyword arguments:

    rank := specifies the maximum rank of the matrix

  '''

  def __init__(self, matrix, **kwargs):

    # save original matrix
    self.matrix = matrix

    # parse keywords
    self.rank = min(kwargs.get("rank", 100), matrix.shape[0], matrix.shape[1])

    # cache set of relations
    self.relations = set()
    for direction, relation, concept in matrix.col_labels:
      self.relations.add(relation)

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

class SampledKB(Knowledgebase):

  def __init__(self, matrix, **kwargs):
    Knowledgebase.__init__(self, matrix, **kwargs)

    # sample SVD at equisdtanced dimensions along in [1,rank]

class ExactKB(Knowledgebase):

  def __init__(self, matrix, **kwargs):
    Knowledgebase.__init__(self, matrix, **kwargs)

    # cache results of SVD at maximum rank
    self.u, self.s, self.v = matrix.svd(k=self.rank)
    self.A_k = ReconstructedMatrix(self.u.dot(numpy.diag(self.s)), self.v.T)
    T = self.u.dot(numpy.diag(self.s))
    self.concept_sim = divisi2.reconstructed.reconstruct_symmetric(self.u.dot(numpy.diag(self.s)))
    self.feature_sim = divisi2.reconstructed.reconstruct_symmetric(self.v.dot(numpy.diag(self.s)))

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
    return sum([self.get_assertion_truth_delta(i, j, d) for d in xrange(k+1)])

  def get_concept_similarity(self, c1, c2, k):
    i = self.u.row_index(c1)
    j = self.u.row_index(c2)
    return sum([self.get_concept_similarity_delta(i, j, d) for d in xrange(k)])

  def get_feature_similarity(self, f1, f2, k):
    if f1 not in self.v.row_labels or f2 not in self.v.row_labels:
      return 0
    i = self.v.row_index(f1)
    j = self.v.row_index(f2)
    return sum([self.get_feature_similarity_delta(i, j, d) for d in xrange(k)])

  # use value of row as if SVD was computed at rank=k

  def get_similar_concepts(self, c, k, n):
    if c not in self.concept_sim.row_labels:
      return []
    return [c for c, v in self.concept_sim.row_named(c).top_items(n=n)]
    # concepts = self.get_concepts()
    # get_sim = lambda c2: self.get_concept_similarity(c, c2, k)
    # items = sorted([(get_sim(c2), c2) for c2 in concepts], reverse=True)[:n]
    # return [b for a, b in items]

  def get_similar_features(self, f, k, n):
    if f not in self.feature_sim.row_labels:
      return []
    return [f for f, v in self.feature_sim.row_named(f).top_items(n=n)]
    # features = self.get_features()
    # get_sim = lambda f2: self.get_feature_similarity(f, f2, k)
    # items = sorted([(get_sim(f2), f2) for f2 in features], reverse=True)[:n]
    # return [b for a, b in items]

  def get_similar_assertions(self, a, k, n):
    c1, r, c2 = a
    similar_left_concepts = self.get_similar_concepts(c1, k, n)
    similar_right_concepts = self.get_similar_concepts(c2, k, n)
    similar_left_features = self.get_similar_features(('left', r, c1), k, n)
    similar_right_features = self.get_similar_features(('right', r, c2), k, n)
    assertions = []
    for left_concept in similar_left_concepts:
      for right, r, right_concept in similar_right_features:
        assertions.append((left_concept, r, right_concept))
    for right_concept in similar_right_concepts:
      for left, r, left_concept in similar_left_features:
        assertions.append((left_concept, r, right_concept))
    return assertions[:n]

  def get_top_concepts(self, f, k, n):
    return [c for c, v in self.A_k.col_named(f).top_items(n=n)]

  def get_top_features(self, c, k, n):
    return [f for f, v in self.A_k.row_named(c).top_items(n=n)]

  # returns list of answer to question at each dimension

  def get_assertion_truth_coeffs(self, a):
    c1, r, c2 = a
    feature = ('right', r, c2)
    i = self.u.row_index(c1)
    if feature not in self.v.row_labels:
      return [0]
    j = self.v.row_index(feature)
    get_delta = lambda d: self.get_assertion_truth_delta(i, j, d)
    return self._get_coeffs(get_delta)

  def get_concept_similarity_coeffs(self, c1, c2):
    i = self.u.row_index(c1)
    j = self.u.row_index(c2)
    get_delta = lambda d: self.get_concept_similarity_delta(i, j, d)
    return self._get_coeffs(get_delta)

  def get_feature_similarity_coeffs(self, f1, f2):
    i = self.v.row_index(f1)
    j = self.v.row_index(f2)
    get_delta = lambda d: self.get_feature_similarity_delta(i, j, d)
    return self._get_coeffs(get_delta)

  def get_assertion_similarity_coeffs(self, a1, a2):
    def get_index(x, labels):
      if x in labels:
        return labels.index(x)
      else:
        return None
    def get_delta(d):

      # deconstruct assertions
      left_c1, r1, right_c1 = a1
      left_c2, r2, right_c2 = a2

      # form features
      left_f1 = ('left', r1, left_c1)
      right_f1 = ('right', r1, right_c1)
      left_f2 = ('left', r2, left_c2)
      right_f2 = ('right', r2, right_c2)

      # get indices
      left_c1_i = get_index(left_c1, self.matrix.row_labels)
      right_c1_i = get_index(right_c1, self.matrix.row_labels)
      left_c2_i = get_index(left_c2, self.matrix.row_labels)
      right_c2_i = get_index(right_c2, self.matrix.row_labels)
      left_f1_i = get_index(left_f1, self.matrix.col_labels)
      right_f1_i = get_index(right_f1, self.matrix.col_labels)
      left_f2_i = get_index(left_f2, self.matrix.col_labels)
      right_f2_i = get_index(right_f2, self.matrix.col_labels)

      # aggregate mappings, zeroing out useless queries
      left_c_delta = 0 if None in (left_c1_i, left_c2_i) else\
        self.get_concept_similarity_delta(left_c1_i, left_c2_i, d)
      right_c_delta = 0 if None in (right_c1_i, right_c2_i) else\
        self.get_concept_similarity_delta(right_c1_i, right_c2_i, d)
      left_f_delta = 0 if None in (left_f1_i, left_f2_i) else\
        self.get_feature_similarity_delta(left_f1_i, left_f2_i, d)
      right_f_delta = 0 if None in (right_f1_i, right_f2_i) else\
        self.get_feature_similarity_delta(right_f1_i, right_f2_i, d)

      return 4 * left_c_delta * right_c_delta * left_f_delta * right_f_delta /\
        (left_c_delta + right_c_delta + left_f_delta + right_f_delta)

    return self._get_coeffs(get_delta)

  # helper function to accrue cumulative sum of deltas

  def _get_coeffs(self, get_delta):
    total = 0
    values = []
    for d in xrange(self.rank):
      total += get_delta(d)
      values.append(total)
    coeffs = numpy.polyfit(range(self.rank), values, self.rank - 1)
    return coeffs

# global current instance of the knowledgebase
kb = None

def init_model():
  global kb
  c4 = divisi2.network.conceptnet_matrix('en')
  kb = ExactKB(c4, rank=20)
  # m = create_sparse_matrix([["a", "r", "x"], ["a", "r", "y", 20], ["b", "r", "x", 5]])
  # kb = ExactKB(m, rank=4)
