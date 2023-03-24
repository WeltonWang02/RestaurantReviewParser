from gensim.models import KeyedVectors
from sanic import Sanic
from sanic import response
from dotenv import load_dotenv
load_dotenv()
from sanic.exceptions import SanicException, ServerError, NotFound
from reviews import *
import os
from sanic.worker.manager import WorkerManager
WorkerManager.THRESHOLD = 1000

model = KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)

class FailedHTTPResponse(Exception):
    "Raised when zembra returns an failed response"
    pass

app = Sanic(__name__)
@app.route("/", methods=['POST', 'GET'])
async def easter(request):
    return response.text('{"response":"Invalid endpoint"}')
  
@app.route("/api/v1/fetch/", methods=['POST', 'GET'])
async def analysis(request):
    if request.method == 'POST':
        request_json = request.json
        pred = Restaurant(request_json['location'], model)
        pred.fetch_reviews(int(os.environ['REVIEW_COUNT']))
        pred.process_review_data()
        res = pred.return_rankings()
        parsed_data = [(x[0], x[1]['agg'], x[1]['matches']) for x in res]
        return response.json({'response':"Success", "list":parsed_data})
    else:
        return response.json({"response":"Invalid response method"})

@app.exception(NotFound)
async def manage_not_found(request, exception):
    return response.text('{"response":"Invalid endpoint"}')


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int(os.environ['PORT']),
    )
