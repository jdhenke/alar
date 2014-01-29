import divisi2, os
from divisi2 import OrderedSet, DenseMatrix, SparseMatrix
from divisi2.reconstructed import ReconstructedMatrix, reconstruct_symmetric
import numpy as np
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
    assertions := list of (concept1, relation, concept2) tuples

  '''

  def __init__(self, matrix, **kwargs):

    # save original matrix
    self.matrix = matrix

    # parse keywords

    # rank is minimum of given, height, width of matrix. given defaults to 100.
    self.rank = min(kwargs.get("rank", 100), matrix.shape[0], matrix.shape[1])

    # assertions
    # self.assertions = kwargs["assertions"]

    # cache set of relations
    self.relations = set()
    for direction, relation, concept in matrix.col_labels:
      self.relations.add(relation)

    # helper for creating similarity matrices at all ranks [1,rank]
    def get_row_similarity_matrices(mat):
      # normalizes rows to norm 1 and zero means columns to maximize variance
      print '\tNormalizing rows'
      normalized_matrix = mat.T.normalize_cols().T

      print '\tNormalizing dimensions'
      # normalized_matrix = normalized_matrix.col_mean_center()[0]
      print normalized_matrix
      self.test = normalized_matrix

      print '\tPerforming SVD'
      # svd of normalized matrix
      u, s, v = normalized_matrix.svd(k=self.rank)
      print s
      original_s = s.copy()
      # output
      print '\tReconstructing matrices'
      similarity_matrices = {}
      for sub_rank in xrange(self.rank, 0, -1):
        if sub_rank < self.rank: s[sub_rank] = 0.0
        # projection of each row vector into eigen space i.e. PCA
        # \[ U \Sigma = A V \]
        pca = u.dot(np.diag(s))
        # (scaled?) covariance matrix
        # A A^T = U \Sigma V^T V \Sigma^T U^T = (U \Sigma) (U \Sigma)^T = PCA PCA^T
        sim_matrix = reconstruct_symmetric(pca)
        similarity_matrices[sub_rank] = sim_matrix

      return u, original_s, v, similarity_matrices

    # create cached results for concept similarities
    print "Creating concept similarity matrices"
    self.concept_u, self.concept_s, self.concept_v, self.concept_sims =\
      get_row_similarity_matrices(matrix)

    # create cached results for feature similarities
    print "Creating feature similarity matrices"
    self.feature_u, self.feature_s, self.feature_v, self.feature_sims =\
      get_row_similarity_matrices(matrix.T)

    # create cached results for assertion estimates/similarities
    print "Creating assertion inference matrices"
    self.assertion_truths = {}
    u, s, v = self.assertion_u, self.assertion_s, self.assertion_v =\
      matrix.svd(k=self.rank)
    for sub_rank in xrange(self.rank, 0, -1):
      if sub_rank < self.rank: s[sub_rank] = 0
      pca = u.dot(np.diag(s))
      self.assertion_truths[sub_rank] = ReconstructedMatrix(pca, v.T)

    # # create cached results for assertion similarities
    # print "Creating assertion similarity matrices"
    # return
    # # create a matrix with assertions as rows and deltas per dimension as cols
    # assertion_data = []
    # assertion_labels = OrderedSet([])
    # dimension_labels = ["delta @ %i" % (d,) for d in range(1, self.rank + 1)]
    # for i in xrange(self.get_num_concepts()):
    #   for j in xrange(self.get_num_features()):
    #     c1 = self.matrix.row_labels[i]
    #     d, r, c2 = self.matrix.col_labels[j]
    #     assertion_label = "%s %s %s" %\
    #       ((c1, r, c2, ) if d == "right" else (c2, r, c1, ))
    #     if assertion_label in assertion_labels:
    #       continue
    #     assertion_labels.append(assertion_label)
    #     row = []
    #     for k in range(self.rank):
    #       row.append(self.get_assertion_truth_delta(i, j, k))
    #     assertion_data.append(row)
    # self.assertion_matrix = DenseMatrix(assertion_data,
    #                                     row_labels=assertion_labels,
    #                                     col_labels=dimension_labels)
    # self.assertion_matrix = self.assertion_matrix.normalize_rows()
    # self.assertion_matrix = self.assertion_matrix.col_mean_center()[0]
    # self.assertion_sim_u, self.assertion_sim_s, self.assertion_sim_v =\
    #   self.assertion_matrix.svd()

    print "Knowledgebase created."

  # O(1) size features

  def get_num_assertions(self):
    return self.matrix.nnz

  def get_num_concepts(self):
    return self.matrix.shape[0]

  def get_num_features(self):
    return self.matrix.shape[1]

  def get_rank(self):
    return self.rank

  # checks if assertion was included originally

  def is_original_assertion(self, a):
    c1, r, c2 = a
    return self.matrix.entry_named(c1, ('right', r, c2)) != 0.0

  # entity list accessors, mostly needed for typeahead

  def get_concepts(self):
    return self.matrix.row_labels

  def get_features(self):
    return self.matrix.col_labels

  def get_relations(self):
    return self.relations

  def get_assertions(self):
    return self.assertions

  # get contribution of each dimension to the following

  def get_assertion_truth_delta(self, i, j, d):
    u, s, v = self.assertion_u, self.assertion_s, self.assertion_v
    return u[i][d] * s[d] * v[j][d]

  def get_concept_similarity_delta(self, i, j, d):
    u, s, v = self.concept_u, self.concept_s, self.concept_v
    return u[i][d] * (s[d] ** 2) * u[j][d]

  def get_feature_similarity_delta(self, i, j, d):
    u, s, v = self.feature_u, self.feature_s, self.feature_v
    return u[i][d] * (s[d] ** 2) * u[j][d]

  def get_assertion_similarity_delta(self, i, j, d):
    u, s, v = self.assertion_sim_u, self.assertion_sim_s, self.assertion_sim_v
    return u[i][d] * (s[d] ** 2) * u[j][d]

  # get value of single cell as if SVD was computed at rank=k

  def get_assertion_truth(self, a, k):
    c1, r, c2 = a
    feature = ('right', r, c2)
    return self.assertion_truths[k].entry_named(c1, feature)

  def get_concept_similarity(self, c1, c2, k):
    return self.concept_sims[k].entry_named(c1, c2)

  def get_feature_similarity(self, f1, f2, k):
    if f1 not in self.matrix.col_labels or f2 not in self.v.col_labels:
      return 0
    return self.feature_sims[k].entry_named(f1, f2)

  # use value of row as if SVD was computed at rank=k

  def get_similar_concepts(self, c, k, n):
    return [c2 for c2, v in self.concept_sims[k].row_named(c).top_items(n=n)]

  def get_similar_features(self, f, k, n):
    return [f for f, v in self.feature_sims[k].row_named(f).top_items(n=n)]

  def get_similar_assertions(self, a, k, n):
    # TODO: make better heuristic
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
    return [c for c, v in self.assertion_truths[k].col_named(f).top_items(n=n)]

  def get_top_features(self, c, k, n):
    return [f for f, v in self.assertion_truths[k].row_named(c).top_items(n=n)]

  # returns list of answer to question at each dimension

  def get_assertion_truth_coeffs(self, a):
    c1, r, c2 = a
    feature = ('right', r, c2)
    i = self.matrix.row_index(c1)
    if feature not in self.matrix.col_labels:
      return [0]
    j = self.matrix.col_index(feature)
    get_delta = lambda d: self.get_assertion_truth_delta(i, j, d)
    return self._get_coeffs(get_delta)

  def get_concept_similarity_coeffs(self, c1, c2):
    i = self.matrix.row_index(c1)
    j = self.matrix.row_index(c2)
    get_delta = lambda d: self.get_concept_similarity_delta(i, j, d)
    return self._get_coeffs(get_delta)

  def get_feature_similarity_coeffs(self, f1, f2):
    if f1 not in self.matrix.col_labels or f2 not in self.matrix.col_labels:
      return [0]
    i = self.matrix.col_index(f1)
    j = self.matrix.col_index(f2)
    get_delta = lambda d: self.get_feature_similarity_delta(i, j, d)
    return self._get_coeffs(get_delta)

  # def get_assertion_similarity_coeffs(self, a1, a2):
  #   def get_index(x, labels):
  #     if x in labels:
  #       return labels.index(x)
  #     else:
  #       return None
  #   def get_delta(d):

  #     # deconstruct assertions
  #     left_c1, r1, right_c1 = a1
  #     left_c2, r2, right_c2 = a2

  #     # form features
  #     left_f1 = ('left', r1, left_c1)
  #     right_f1 = ('right', r1, right_c1)
  #     left_f2 = ('left', r2, left_c2)
  #     right_f2 = ('right', r2, right_c2)

  #     # get indices
  #     left_c1_i = get_index(left_c1, self.matrix.row_labels)
  #     right_c1_i = get_index(right_c1, self.matrix.row_labels)
  #     left_c2_i = get_index(left_c2, self.matrix.row_labels)
  #     right_c2_i = get_index(right_c2, self.matrix.row_labels)
  #     left_f1_i = get_index(left_f1, self.matrix.col_labels)
  #     right_f1_i = get_index(right_f1, self.matrix.col_labels)
  #     left_f2_i = get_index(left_f2, self.matrix.col_labels)
  #     right_f2_i = get_index(right_f2, self.matrix.col_labels)

  #     # aggregate mappings, zeroing out useless queries
  #     left_c_delta = 0 if None in (left_c1_i, left_c2_i) else\
  #       self.get_concept_similarity_delta(left_c1_i, left_c2_i, d)
  #     right_c_delta = 0 if None in (right_c1_i, right_c2_i) else\
  #       self.get_concept_similarity_delta(right_c1_i, right_c2_i, d)
  #     left_f_delta = 0 if None in (left_f1_i, left_f2_i) else\
  #       self.get_feature_similarity_delta(left_f1_i, left_f2_i, d)
  #     right_f_delta = 0 if None in (right_f1_i, right_f2_i) else\
  #       self.get_feature_similarity_delta(right_f1_i, right_f2_i, d)

  #     return 4 * left_c_delta * right_c_delta * left_f_delta * right_f_delta /\
  #       (left_c_delta + right_c_delta + left_f_delta + right_f_delta)

  #   return self._get_coeffs(get_delta)

  def get_assertion_similarity_coeffs(self, a1, a2):
    if a1 not in self.assertion_matrix.row_labels or\
       a2 not in self.assertion_matrix.row_labels:
       return [0]
    i = self.assertion_matrix.row_index(a1)
    j = self.assertion_matrix.row_index(a2)
    get_delta = lambda d: self.get_assertion_similarity_delta(i, j, d)
    return self._get_coeffs(get_delta)

  # helper function to get polynomial fit to curve of sum of deltas

  def _get_coeffs(self, get_delta):
    total = 0
    values = []
    for d in xrange(self.rank):
      total += get_delta(d)
      values.append(total)
    print values
    coeffs = np.polyfit(range(self.rank), values, self.rank - 1)
    return coeffs

# global current instance of the knowledgebase
kb = None

def init_model():
  global kb
  # kb = create_kb_from_text(open("assertions.txt").read())
  c4 = divisi2.network.conceptnet_matrix('en')
  kb = Knowledgebase(c4, rank=100)


def create_kb_from_text(text):
  assertions = filter(lambda x: len(x) in {3,4},
                      map(lambda L: L.strip().lower().split(),
                          text.split(os.linesep)))
  m = create_sparse_matrix(assertions)
  return Knowledgebase(m, assertions=[a[:3] for a in assertions])

## Debugging

# p = np.poly1d(kb.get_concept_similarity_coeffs("coffee", "drink"))
# print [p(x) for x in xrange(kb.rank)]
if __name__ == '__main__':
  init_model()

