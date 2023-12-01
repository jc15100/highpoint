'''
Interface to define a contract for Highlights module.
'''
class Highlights:
    '''
    Given a list of frames & a decision boundary, select the frames and return those that constitute a highlight.
    '''
    def highlights(self, frames, boundary=0.5, skip=False):
        pass