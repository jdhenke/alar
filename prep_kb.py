import argparse, csv, os, pickle
import numpy as np
from numpy.linalg import norm
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import svds

def main():
  # parse arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("file", help="csv file of assertions")
  args = parser.parse_args()
  fname = parser.parse_args().file
  assert os.path.isfile(fname), "invalid file given"
  # get assertions from file
  assertions = get_assertions(fname)
  print "%i unique assertions found." % (len(assertions), )
  print "Creating raw assertion matrix..."
  raw_matrix, row_labels, col_labels, relations = create_matrix(assertions)
  rank = min(len(row_labels)-1, len(col_labels)-1, 100)
  print "Using maximum rank of %i." % (rank, )
  print "Normalizing for concepts..."
  write_concept_svd(raw_matrix, rank)
  print "Normalizing for features..."
  write_feature_svd(raw_matrix, rank)
  print "Normalizing for assertions..."
  write_assertion_svd(raw_matrix, rank)
  print "Saving relations..."
  save(relations, "relations.pkl")
  print "Saving row labels..."
  save(row_labels, "concepts.pkl")
  print "Saving column labels..."
  save(col_labels, "features.pkl")
  print "Saving assertions..."
  save(assertions, "assertions.pkl")
  print "Done."

def get_assertions(fname):
  assertions = set()
  normalized_text = lambda text: text.lower().replace(" ", "_")
  with open(fname, 'rb') as csvfile:
    r = csv.reader(csvfile)
    for row in r:
      assert (len(row) in (3,4)), "invalid number of columns"
      assertions.add(tuple(map(normalized_text, row)))
  return assertions

def create_matrix(assertions, right=True, left=True):
  row_labels, col_labels = [], []
  concept_dict, feature_dict = {}, {}
  rows, cols, data = [], [], []
  relations = set()
  def add_entry(concept, feature, truth):
    if concept not in concept_dict:
      concept_dict[concept] = len(row_labels)
      row_labels.append(concept)
    if feature not in feature_dict:
      feature_dict[feature] = len(col_labels)
      col_labels.append(feature)
    rows.append(concept_dict[concept])
    cols.append(feature_dict[feature])
    data.append(float(truth))
  for a in assertions:
    c1, r, c2 = a[:3]
    truth = 1.0
    if len(a) == 4:
      truth = a[3]
    if right: add_entry(c1, ('right', r, c2), truth)
    if left: add_entry(c2, ('left', r, c1), truth)
    relations.add(r)
  mat = coo_matrix((data, (rows, cols))).tocsc()
  return mat, row_labels, col_labels, relations

def write_concept_svd(raw_matrix, rank):
  norm_matrix = normalize_rows(raw_matrix)
  write_svd(norm_matrix, rank, "concept")

def write_feature_svd(raw_matrix, rank):
  norm_matrix = normalize_rows(raw_matrix.T).T
  write_svd(norm_matrix, rank, "feature")

def write_assertion_svd(raw_matrix, rank):
  norm_matrix = raw_matrix
  write_svd(norm_matrix, rank, "assertion")

def write_svd(norm_matrix, rank, prefix):
  u,s,vt = svds(norm_matrix, k=rank)
  u = u[:,::-1][:,:rank]
  s = s[::-1][:rank]
  v = vt.T[:,::-1][:,:rank]
  for mat, name in ((u, 'u'), (s, 's'), (v, 'v')):
    np.save("%s_%s.npy" % (prefix, name, ), mat)

def normalize_rows(mat):
  return mat
  print type(mat)
  norms = map(norm, mat[:])
  return mat / np.array(norms)[:,None]

def save(obj, fname):
  fname = "%s" % (fname, )
  with open(fname, "w") as f:
    pickle.dump(obj, f)

if __name__ == '__main__':
  main()
