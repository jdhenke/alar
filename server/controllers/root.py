from pecan import expose, redirect
from webob.exc import status_map
import simplejson
from server import model

class KBController(object):

    @expose('json')
    def get_dimensionality_bounds(self):
        return {"min": 1, "max": 100}

    @expose('json')
    def get_concepts(self):
        return ['pizza', 'food']

    @expose('json')
    def get_relations(self):
        return ['is']

    @expose('json')
    def get_links(self):
        return []

    @expose('json')
    def get_linked_nodes(self):
        return []

    @expose('json')
    def get_truth(self):
        return {'truth_coeffs': [0.01,0]}


class RootController(object):

    @expose()
    def index(self):
        redirect("/summary")

    @expose(generic=True, template='edit.html')
    def edit(self):
        return {
            "assertions": simplejson.dumps(["pizza", "isa", "food", 69]),
            "dimensions": str([10,50,100]),
        }

    @edit.when(method='POST')
    @expose('json')
    def edit_post(self, assertions, dimensions):
        redirect('/summary')

    @expose(template='summary.html')
    def summary(self):
        return {}

    @expose(template='explore.html')
    def explore(self):
        return {}

    @expose('json')
    def test(self):
        print model.kb
        return 1


    @expose('error.html')
    def error(self, status):
        try:
            status = int(status)
        except ValueError:  # pragma: no cover
            status = 500
        message = getattr(status_map.get(status), 'explanation', '')
        return dict(status=status, message=message)

    kb = KBController()
