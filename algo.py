import numpy as np
import heapq

from close_cross_product import get_closest_product_indices

# constants
m, n, r, k = 22 ,110, 10, 10

# create svd
A = np.random.rand(m, n)
u,s,vt = np.linalg.svd(A)
u = u[:,:r]
s = s[:r]
v = vt.T[:,:r]
v0 = np.random.rand(r)

# main algorithm to find truest assertions consider first d dimensions
# for all d [0, r)
def algo(assertion_vec):
  output = []
  top_per_dim = list(create_linked_top_per_dim(assertion_vec))
  running_top = []
  memo = set()
  best_val_at_dim = {}
  for d in xrange(r):
    def get_val(i, j):
      return 0 - (u[i,:d+1] * v[j, :d+1]).dot(assertion_vec[:d+1])
    def extract():
      for dim, gen in enumerate(top_per_dim):
        try:
          i, j = gen.next()
          val = get_val(i, j)
          best_val_at_dim[dim] = u[i, dim] * v[j, dim] * assertion_vec[dim]
          if (i, j) not in memo:
            memo.add((i,j))
            heapq.heappush(running_top, [val, (i, j)])
        except StopIteration:
          pass
    def get_max_best_from_gens():
      return sum([best_val_at_dim[dim] for dim in xrange(r)])

    best_to_d = []
    for item in running_top:
      i, j = item[1]
      item[0] -= u[i, d] * v[j, d] * assertion_vec[d]
    heapq.heapify(running_top)

    extract()
    while len(best_to_d) < k:
      while 0 - running_top[0][0] < get_max_best_from_gens():
        extract()
      best_to_d.append(heapq.heappop(running_top))

    output.append([indices for _, indices in best_to_d])
    for x in best_to_d:
      heapq.heappush(running_top, x)

  return output

# generates generators of truest assertions for a single dimension
def create_linked_top_per_dim(vec):
  for d in xrange(r):
    yield create_top_at_dim(vec, d)

# generates truest assertions only considering dimension=d
def create_top_at_dim(vec, d):
  ud = sorted([(val, index) for index, val in enumerate(u[:,d])])
  vd = sorted([(val, index) for index, val in enumerate(v[:,d])])
  ud.sort()
  vd.sort()

  get_val = lambda i, j: 0 - vec[d] * ud[i][0] * vd[j][0]
  def get_increasing_next_indices(i, j):
    if i + 1 < len(ud):
      yield i + 1, j
    if j + 1 < len(vd):
      yield i, j + 1
  def get_decreasing_next_indices(i, j):
    if i - 1 >= 0:
      yield i - 1, j
    if j - 1 >= 0:
      yield i, j - 1

  # stores min heap of [(0 - val, indices), ... ]
  h = []
  heapq.heappush(h, (get_val(0, 0), (0, 0), get_increasing_next_indices))
  heapq.heappush(h, (get_val(m - 1, n - 1),
                     (m - 1, n - 1),
                     get_decreasing_next_indices))
  memo = {(0, 0), (len(ud) - 1, len(vd) - 1)}
  while len(h) > 0:
    neg_val, indices, get_next_indices = heapq.heappop(h)
    yield ud[indices[0]][1], vd[indices[1]][1]
    for next_indices in get_next_indices(*indices):
      if next_indices not in memo:
        memo.add(next_indices)
        heapq.heappush(h, (get_val(*next_indices),
                           next_indices,
                           get_next_indices))

# check answers
if __name__ == '__main__':

  print "Running algo..."
  top_to_dim = algo(v0)
  print "Done."

  assertion_vectors = []
  for i in xrange(m):
    for j in xrange(n):
      assertion_vectors.append(u[i] * v[j])
  assertion_vectors = np.array(assertion_vectors)

  for d in xrange(r):
    sims_up_to_d = assertion_vectors[:,:d+1].dot(v0[:d+1])
    items = [(val, index) for (index, val) in enumerate(sims_up_to_d)]
    items.sort(reverse=True)
    solution = [(index // n, index % n) for (_, index) in items[:k]]
    if solution != top_to_dim[d]:
      print "Differences at dim=%i\nResult: %s\nSolution: %s" %\
        (d, top_to_dim[d], solution)
      print [(u[i,:d+1]*v[j,:d+1]).dot(v0[:d+1]) for i, j in top_to_dim[0]]
      print [(u[i,:d+1]*v[j,:d+1]).dot(v0[:d+1]) for i, j in solution]
      assert False

  print "Passed!"
