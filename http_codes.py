class GCHttpCode():
    code = 200
    message = None


class HttpCreated(GCHttpCode):
    code = 201

    def __init__(self, message=None):
        self.message = message


class HttpEmpty(GCHttpCode):
    code = 204