from Products.Five import BrowserView

class UnauthorizedView(BrowserView):
    """
    View of an Unauthorized exception that simply reraises it, so that it can
    be handled by the response and trigger the PAS challenge plugin,
    rather than be rendered using the standard_error_message.
    
    This can be removed once the exception handling in the ZPublisher is
    corrected.
    """
    
    def __call__(self):
        # self.context is the original Unauthorized exception
        raise self.context
