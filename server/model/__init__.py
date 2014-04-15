import heapq, pickle, warnings
import numpy as np

norm = np.linalg.norm
warnings.simplefilter('ignore', np.RankWarning)

class Knowledgebase(object):

  def __init__(self):
    self.original_assertions = pickle.load(open("assertions.pkl"))
    self.concepts = pickle.load(open("concepts.pkl"))
    self.features = pickle.load(open("features.pkl"))
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
    concept_index = self.concepts.index(c)
    reduced_concept_vector = reduced_concept_pca[concept_index]
    sims = reduced_concept_pca.dot(reduced_concept_vector)
    return top_items(sims, self.concepts, n)

  def get_similar_features(self, f, k, n):
    u, s, v = self.feature_svd
    reduced_feature_pca = normalize_rows((v*s)[:,:k])
    feature_index = self.features.index(f)
    reduced_feature_vector = reduced_feature_pca[feature_index]
    sims = reduced_feature_pca.dot(reduced_feature_vector)
    return top_items(sims, self.features, n)

  def get_similar_assertions(self, a, k, n):
    c1, r, c2 = a
    u, s, v = self.assertion_svd
    vecs = []
    labels = []
    for c in self.concepts:
      vecs.append(self._get_assertion_vector((c, r, c2)))
      labels.append((c, r, c2))
      vecs.append(self._get_assertion_vector((c1, r, c)))
      labels.append((c1, r, c))
    for feature in self.features:
      d, r, c = feature
      if d == 'right':
        vecs.append(self._get_assertion_vector((c1, r, c)))
        labels.append((c1, r, c))
      else:
        vecs.append(self._get_assertion_vector((c, r, c2)))
        labels.append((c, r, c2))
    red_assertion_vecs = normalize_rows(np.asarray(vecs)[:,:k])
    assertion_index = labels.index(a)
    reduced_assertion_vector = red_assertion_vecs[assertion_index]
    sims = red_assertion_vecs.dot(reduced_assertion_vector)
    return top_items(sims, labels, n)

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
    u, s, v = self.concept_svd
    try:
      index = self.concepts.index(c)
      return (u*s)[index]
    except ValueError:
      return np.zeros(self.rank)

  def _get_feature_vector(self, f):
    u, s, v = self.feature_svd
    try:
      index = self.features.index(f)
      return (v*s)[index]
    except ValueError:
      return np.zeros(self.rank)

  def _get_assertion_vector(self, a):
    u, s, v = self.assertion_svd
    c1, r, c2 = a
    try:
      concept_index = self.concepts.index(c1)
      feature_index = self.features.index(('right', r, c2))
      return (u*s)[concept_index] * v[feature_index]
    except ValueError:
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
  kb = Knowledgebase()
