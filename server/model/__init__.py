import pickle, warnings
import numpy as np

norm = np.linalg.norm
warnings.simplefilter('ignore', np.RankWarning)

class Knowledgebase(object):

  def __init__(self):
    print "Loading original assertions..."
    self.original_assertions = pickle.load(open("assertions.pickle"))
    print "Loading PCA tuned for concepts..."
    self.concept_pca = pickle.load(open("concept_pca.pickle"))
    print "Loading SVD tuned for assertions..."
    self.assertion_svd = pickle.load(open("assertion_svd.pickle"))
    self.rank = self.concept_pca.shape[1]
    print "Knowledgebase created."


  ### get origin of assertion

  def is_original_assertion(self, a):
    return a in self.original_assertions

  ### get lists of similar entities

  def get_similar_concepts(self, c, k, n):
    reduced_concept_pca = self.concept_pca[:,:k].normalize_rows()
    reduced_concept_vector = reduced_concept_pca.row_named(c)
    sims = reduced_concept_pca.dot(reduced_concept_vector)
    for c, _ in sims.top_items(n=n): yield c

  def get_similar_assertions(self, a, k, n):
    us, v = self.assertion_svd
    i, j = us.row_index(a[0]), v.row_index(('right', ) + a[1:])
    concept_vecs, feature_vecs = us[:,:k], v[:,:k]
    for f, _ in feature_vecs.dot(concept_vecs[i]).top_items(n=n//2):
      yield a[:1] + f[1:]
    for c, _ in concept_vecs.dot(feature_vecs[j]).top_items(n=n//2):
      yield (c,) + a[1:]

  ### get coefficients of polynomial in dimensionality

  def get_concept_similarity_coeffs(self, c1, c2):
    v1, v2 = map(self._get_concept_vector, (c1, c2))
    return self._interpolate(lambda d: norm_dot(v1[:d], v2[:d]))

  def get_assertion_similarity_coeffs(self, a1, a2):
    v1, v2 = map(self._get_assertion_vector, (a1, a2))
    return self._interpolate(lambda d: norm_dot(v1[:d], v2[:d]))

  def get_assertion_truth_coeffs(self, a):
    vec = self._get_assertion_vector(a)
    return self._interpolate(lambda d: np.sum(vec[:d]))

  ### helper functions

  def _get_concept_vector(self, c):
    return self.concept_pca.row_named(c)

  def _get_assertion_vector(self, a):
    try:
      us, v = self.assertion_svd
      i, j = us.row_index(a[0]), v.row_index(('right', ) + a[1:])
      return us[i] * v[j]
    except KeyError:
      return np.zeros(self.rank)

  def _interpolate(self, f):
    values = map(f, xrange(1, self.rank + 1))
    return np.polyfit(range(self.rank), values, self.rank - 1)

def norm_dot(v1, v2):
  norm1, norm2 = map(lambda v: norm(v) if norm(v) > 0 else 1.0, (v1, v2))
  return v1.dot(v2) / (norm1 * norm2)

kb = None
def init_model():

  global kb
  kb = Knowledgebase()
