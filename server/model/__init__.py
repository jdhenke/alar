import divisi2, math, pickle
import numpy as np
norm = np.linalg.norm

class Knowledgebase(object):

  def __init__(self):
    self.rank = 100
    print "Loading original assertions..."
    self.original_assertions =\
      pickle.load(open("original_assertions.pickle"))
    print "Loading PCA tuned for concepts..."
    self.concept_pca = pickle.load(open("concept_pca.pickle"))
    print "Loading SVD tuned for assertions..."
    self.assertion_svd = pickle.load(open("assertion_svd.pickle"))
    print "Knowledgebase created."

  ### get origin of assertion

  def is_original_assertion(self, a):
    return tuple(a) in self.original_assertions

  ### get lists of similar entities

  def get_similar_concepts(self, c, k, n):
    reduced_concept_pca = self.concept_pca[:,:k].normalize_rows()
    reduced_concept_vector = reduced_concept_pca.row_named(c)
    sims = reduced_concept_pca.dot(reduced_concept_vector.T)
    return [c for c, v in sims.top_items(n=n)]

  def get_similar_assertions(self, a, k, n):
    concept_pca, v = self.assertion_svd
    i = concept_pca.row_index(a[0])
    j = v.row_index(('right', ) + a[1:])
    concept_vectors = concept_pca[:,:k].normalize_rows()
    feature_vectors = v[:,:k].normalize_rows()
    top_feature_items = feature_vectors.dot(concept_vectors[i]).top_items(n=n//2)
    top_concept_items = concept_vectors.dot(feature_vectors[j]).top_items(n=n//2)
    output = []
    for c, _ in top_concept_items: output.append((c,) + a[1:])
    for f, _ in top_feature_items: output.append(a[:1] + f[1:])
    return output

  ### get coefficients of

  def get_concept_similarity_coeffs(self, c1, c2):
    return self._get_sim_coeffs(*map(self._get_concept_vector, (c1, c2)))

  def get_assertion_similarity_coeffs(self, a1, a2):
    return self._get_sim_coeffs(*map(self._get_assertion_vector, (a1, a2)))

  def get_assertion_truth_coeffs(self, a):
    return self._get_truth_coeffs(self._get_assertion_vector(a))

  ### helper functions

  def _get_concept_vector(self, c):
    return self.concept_pca.row_named(c)

  def _get_assertion_vector(self, a):
    concept_pca, v = self.assertion_svd
    i = concept_pca.row_index(a[0])
    try:
      j = v.row_index(('right', ) + a[1:3])
    except KeyError:
      return np.zeros(self.rank)
    return concept_pca[i] * v[j]

  def _get_sim_coeffs(self, v1, v2):
    get_similarity_at_dim = lambda d: np.dot(*map(normalize_vector, (v1[:d], v2[:d])))
    values = map(get_similarity_at_dim, range(1, self.rank + 1))
    return np.polyfit(range(self.rank), values, self.rank - 1)

  def _get_truth_coeffs(self, v):
    get_truth_at_dim = lambda d: np.sum(v[:d])
    values = map(get_truth_at_dim, range(1, self.rank + 1))
    return np.polyfit(range(self.rank), values, self.rank - 1)

def normalize_vector(vec):
  return vec / norm(vec) if norm(vec) > 0 else vec

kb = None
def init_model():
  global kb
  kb = Knowledgebase()
