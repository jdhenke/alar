import argparse, csv, divisi2, os, pickle
from divisi2 import OrderedSet
from divisi2.sparse import SparseMatrix

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("file", nargs="?", help="csv file of assertions")
  args = parser.parse_args()
  if args.file:
    print "\tUsing %s" % (args.file, )
    fname = parser.parse_args().file
    assert os.path.isfile(fname), "invalid file given"
    assertions = []
    with open(fname, 'rb') as csvfile:
      r = csv.reader(csvfile)
      for row in r:
        assert(len(row) == 3), "invalid number of columns"
        assertions.append(tuple(row))
    print "Using custom KB; \t%i assertions found." % (len(assertions), )
    create_custom_kb(assertions)
  else:
    print "Using conceptnet4"
    create_c4_kb()
  print "Done."

def create_custom_kb(assertions, right=True, left=True):
  print "\tCreating sparse matrix"
  rows, cols, data = [], [], []
  row_labels, col_labels = OrderedSet(), OrderedSet()
  for i, (c1, r, c2) in enumerate(assertions):
    # form right features
    if right:
      row_labels.append(c1)
      f1 = ('right', r, c2)
      col_labels.append(f1)
      rows.append(row_labels.index(c1))
      cols.append(col_labels.index(f1))
      data.append(1.0)
    # form left features
    if left:
      row_labels.append(c2)
      f2 = ('left', r, c1)
      col_labels.append(f2)
      rows.append(row_labels.index(c2))
      cols.append(col_labels.index(f2))
      data.append(1.0)
  mat = SparseMatrix.from_lists(data, rows, cols)
  mat = SparseMatrix(mat, row_labels=row_labels, col_labels=col_labels)
  save_matrix(mat)
  save_assertions(assertions)

def create_c4_kb():
  print "\tLoading C4 matrix"
  mat = divisi2.network.conceptnet_matrix("en")
  save_matrix(mat)
  assertions = []
  for _, concept, feature in mat.named_entries():
    if feature[0] == 'right':
      assertions.append((concept,) + feature[1:])
    else:
      assertions.append(feature[1:][::-1] + (concept, ))
  save_assertions(assertions)

def save_matrix(mat):
  rank = min(len(mat.row_labels), len(mat.col_labels), 100)
  print "\tComputing SVD with rank %i for concepts" % (rank,)
  norm_mat = mat.normalize_rows()
  u, s, _ = norm_mat.svd(k=rank)
  pickle.dump(u*s, open("concept_pca.pickle", "wb"))
  print "\tComputing SVD with rank %i for assertions" % (rank,)
  u,s,v = mat.svd(k=rank)
  pickle.dump((u*s,v), open("assertion_svd.pickle", "wb"))

def save_assertions(assertions):
  pickle.dump(set(assertions), open("assertions.pickle", "wb"))

if __name__ == '__main__':
  main()
