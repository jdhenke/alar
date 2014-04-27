import heapq, pickle, warnings
import numpy as np

norm = np.linalg.norm
warnings.simplefilter('ignore', np.RankWarning)

class Knowledgebase(object):

  def __init__(self):
    self.original_assertions = pickle.load(open("assertions.pkl"))
    self.relations = pickle.load(open("relations.pkl"))
    self.concepts = pickle.load(open("concepts.pkl"))
    self.concept_indices = {v:i for i,v in enumerate(self.concepts)}
    self.features = pickle.load(open("features.pkl"))
    self.feature_indices = {v:i for i,v in enumerate(self.features)}
    self.concept_svd = load_svd("concept")
    self.feature_svd = load_svd("feature")
    self.assertion_svd = load_svd("assertion")
    self.rank = self.concept_svd[0].shape[1]

  ### get origin of assertion

  def is_original_assertion(self, a):
    return a in self.original_assertions

  ### get lists of similar entities

  def get_similar_concepts(self, c, k, n):
    u, s, v = self.concept_svd
    reduced_concept_pca = normalize_rows((u*s)[:,:k])
    concept_index = self.concept_indices[c]
    reduced_concept_vector = reduced_concept_pca[concept_index]
    sims = reduced_concept_pca.dot(reduced_concept_vector)
    return top_items(sims, self.concepts, n)

  def get_similar_features(self, f, k, n):
    u, s, v = self.feature_svd
    reduced_feature_pca = normalize_rows((v*s)[:,:k])
    feature_index = self.feature_indices[f]
    reduced_feature_vector = reduced_feature_pca[feature_index]
    sims = reduced_feature_pca.dot(reduced_feature_vector)
    return top_items(sims, self.features, n)

  def get_similar_assertions(self, a, k, n):
    u, s, v = self.assertion_svd
    concept_index = self.concept_indices[a[0]]
    feature_index = self.feature_indices[('right', ) + a[1:]]
    concept_vecs, feature_vecs = (u*s)[:,:k], (v*s)[:,:k]
    for c in top_items(concept_vecs.dot(concept_vecs[concept_index]), self.concepts, n // 2):
      yield (c,) + a[1:]
    for f in top_items(feature_vecs.dot(feature_vecs[feature_index]), self.features, n // 2):
      if f[0] == 'right':
        yield a[:1] + f[1:]
      else:
        yield (f[2], f[1], a[0])

  ### get coefficients of polynomial in dimensionality

  def get_concept_similarity_coeffs(self, c1, c2):
    v1, v2 = map(self._get_concept_vector, (c1, c2))
    return self._interpolate(lambda d: norm_dot(v1[:d], v2[:d]))

  def get_feature_similarity_coeffs(self, f1, f2):
    v1, v2 = map(self._get_feature_vector, (f1, f2))
    return self._interpolate(lambda d: norm_dot(v1[:d], v2[:d]))

  def get_assertion_similarity_coeffs(self, a1, a2):
    v1, v2 = map(self._get_assertion_vector, (a1, a2))
    return self._interpolate(lambda d: norm_dot(v1[:d], v2[:d]))

  def get_assertion_truth_coeffs(self, a):
    vec = self._get_assertion_vector(a)
    return self._interpolate(lambda d: np.sum(vec[:d]))

  ### helper functions

  def _get_concept_vector(self, c):
    u, s, v = self.concept_svd
    try:
      index = self.concept_indices[c]
      return u[index]*s
    except ValueError:
      return np.zeros(self.rank)

  def _get_feature_vector(self, f):
    u, s, v = self.feature_svd
    try:
      index = self.feature_indices[f]
      return v[index]*s
    except ValueError:
      return np.zeros(self.rank)

  def _get_assertion_vector(self, a):
    u, s, v = self.assertion_svd
    c1, r, c2 = a
    try:
      concept_index = self.concept_indices[c1]
      feature_index = self.feature_indices[('right', r, c2)]
      return u[concept_index] * s * v[feature_index]
    except (ValueError, KeyError):
      return np.zeros(self.rank)

  def _interpolate(self, f):
    values = map(f, xrange(1, self.rank + 1))
    return np.polyfit(range(self.rank), values, self.rank - 1)

def load_svd(prefix):
  u = np.load(prefix + "_u.npy", mmap_mode="r")
  s = np.load(prefix + "_s.npy", mmap_mode="r")
  v = np.load(prefix + "_v.npy", mmap_mode="r")
  return (u, s, v)

def norm_dot(v1, v2):
  norm1, norm2 = map(lambda v: norm(v) if norm(v) > 0 else 1.0, (v1, v2))
  return v1.dot(v2) / (norm1 * norm2)

def top_items(values, labels, n):
  assert len(values) == len(labels)
  items = zip(0-values, labels)
  heapq.heapify(items)
  for _ in xrange(min(len(labels), n)):
    yield heapq.heappop(items)[1]

def normalize_rows(mat):
  norms = map(np.linalg.norm, mat)
  return mat / np.array(norms)[:,None]

kb = None
def init_model():
  global kb
  print "Loading KB from disk..."
  kb = Knowledgebase()
