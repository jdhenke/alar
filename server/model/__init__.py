import divisi2, math, os, pickle, random
from divisi2 import OrderedSet, DenseMatrix, SparseMatrix
from divisi2.reconstructed import ReconstructedMatrix, reconstruct_symmetric
import numpy as np
from pysparse.sparse import PysparseMatrix

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

    # helper for creating similarity matrices at all ranks [1,rank]
    def get_row_similarity_matrices(mat):

      # normalizes rows to norm 1 and zero means columns to maximize variance
      print '\tNormalizing'
      normalized_matrix = mat.normalize_rows().col_mean_center()[0].squish()

      # svd of normalized matrix
      print '\tPerforming SVD'
      u, s, v = normalized_matrix.svd(k=self.rank)
      print s
      original_s = s.copy()

      # output
      print '\tReconstructing matrices'
      similarity_matrices = {}
      for sub_rank in xrange(self.rank, 0, -1):
        if sub_rank < self.rank: s[sub_rank] = 0.0
        # projection of each row vector into eigen space i.e. PCA
        pca = u.dot(np.diag(s)).normalize_rows()
        # (scaled?) covariance matrix
        # A A^T = U \Sigma V^T V \Sigma^T U^T = (U \Sigma) (U \Sigma)^T = PCA PCA^T
        sim_matrix = reconstruct_symmetric(pca)
        similarity_matrices[sub_rank] = sim_matrix

      return u, original_s, v, similarity_matrices

    # # create cached results for concept similarities
    print "Creating concept similarity matrices"
    self.concept_u, self.concept_s, self.concept_v, self.concept_sims =\
      get_row_similarity_matrices(matrix)

    # create cached results for assertion estimates/similarities
    print "Creating assertion inference matrices"
    self.assertion_truths = {}
    u, s, v = self.assertion_u, self.assertion_s, self.assertion_v =\
      matrix.svd(k=self.rank)
    s = s.copy()
    for sub_rank in xrange(self.rank, 0, -1):
      if sub_rank < self.rank: s[sub_rank] = 0
      pca = u.dot(np.diag(s))
      self.assertion_truths[sub_rank] = ReconstructedMatrix(pca, v.T)

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
    f = ('right', r, c2)
    return f in self.matrix.col_labels and self.matrix.entry_named(c1, f) != 0.0

  # entity list accessors, mostly needed for typeahead

  def get_concepts(self):
    return self.matrix.row_labels

  def get_features(self):
    return self.matrix.col_labels

  # get contribution of each dimension to the following

  def get_assertion_truth_delta(self, i, j, d):
    u, s, v = self.assertion_u, self.assertion_s, self.assertion_v
    return u[i][d] * s[d] * v[j][d]

  def get_concept_similarity_delta(self, i, j, d):
    u, s, v = self.concept_u, self.concept_s, self.concept_v
    return u[i][d] * (s[d] ** 2) * u[j][d]

  def get_assertion_similarity_delta(self, i1, j1, i2, j2, d):
    return self.get_assertion_truth_delta(i1, j1, d) *\
           self.get_assertion_truth_delta(i2, j2, d)

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

  # def get_similar_features(self, f, k, n):
  #   return [f for f, v in self.feature_sims[k].row_named(f).top_items(n=n)]

  def get_similar_assertions(self, a, k, n):
    return [a[:1] + f[1:] for f ,v in self.assertion_truths[k].row_named(a[0]).top_items(n=n)] +\
           [(c, ) + a[1:] for c, v in self.assertion_truths[k].col_named(('right', ) + a[1:]).top_items(n=n)]
    # c1, r, c2 = a
    # possible_c1s = self.get_similar_concepts(c1, k, n)
    # possible_c2s = self.get_similar_concepts(c2, k, n)
    # assertions = []
    # for new_c1 in possible_c1s:
    #   for new_c2 in possible_c2s:
    #     assertions.append((new_c1, r, new_c2))
    # return random.sample(assertions, n)

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
    values = [self.concept_sims[d].entry_named(c1, c2) for d in range(1, self.rank+1)]
    if max(values) == 0.0:
      return [0]
    coeffs = np.polyfit(range(self.rank), values, self.rank - 1)
    return coeffs

  def get_assertion_similarity_coeffs(self, a1, a2):
    def get_indices(a):
      c1, r, c2 = a
      f = ('right', r, c2)
      if f not in self.matrix.col_labels:
        return -1, -1
      return self.matrix.row_index(c1), self.matrix.col_index(f)
    i1, j1 = get_indices(a1)
    i2, j2 = get_indices(a2)
    if min(i1, j1, i2, j2) == -1: return [0]
    values = []
    v1, v2 = [], []
    sos1, sos2 = 0, 0
    for d in xrange(self.rank):
      v1.append(self.get_assertion_truth_delta(i1, j1, d))
      v2.append(self.get_assertion_truth_delta(i2, j2, d))
      sos1 += v1[-1] ** 2
      sos2 += v2[-1] ** 2
      if sos1 == 0.0 or sos2 == 0.0:
        values.append(0)
      else:
        norm1 = math.sqrt(sos1)
        norm2 = math.sqrt(sos2)
        values.append(sum([x1 * x2 / (norm1 * norm2) for x1, x2 in zip(v1, v2)]))
    coeffs = np.polyfit(range(self.rank), values, self.rank - 1)
    return coeffs

  # helper function to get polynomial fit to curve of sum of deltas

  def _get_coeffs(self, get_delta):
    total = 0
    values = []
    for d in xrange(self.rank):
      total += get_delta(d)
      values.append(total)
    coeffs = np.polyfit(range(self.rank), values, self.rank - 1)
    return coeffs

# global current instance of the knowledgebase
kb = None

def init_model():
  global kb
  # kb = create_kb_from_text(open("assertions.txt").read())
  c4 = pickle.load(open("c4_norm.pickle", "rb"))
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
  a1 = ('coffee', 'IsA', 'drink')
  a2 = ('tea', 'IsA', 'drink')
  a3 = ('cat', 'IsA', 'animal')
  p1 = np.poly1d(kb.get_assertion_similarity_coeffs(a1, a2))
  p1 = np.poly1d(kb.get_assertion_similarity_coeffs(a1, a3))
