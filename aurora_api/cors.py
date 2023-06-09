class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Allow requests from all origins.
        response['Access-Control-Allow-Origin'] = '258a482125664d88ad94800ecbefa0af.vfs.cloud9.eu-west-2.amazonaws.com'

        # Allow specific headers to be sent.
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        # Allow all HTTP methods to be used.
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'

        return response
