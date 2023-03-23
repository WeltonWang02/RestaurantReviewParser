from concurrent.futures import ThreadPoolExecutor
import openai
import os
import requests 
import time
import unidecode
import os
import json
from scipy import spatial
import numpy as np

openai.api_key = os.environ["OPENAI_API"]
API_KEY = os.environ["ZEMBRA_API"]

class Restaurant():

  def __init__(self, id, w2v_model):
    self.cid = id
    self.w2v = w2v_model

  def __send_review_request(self, limit):
    """
      Send a request to zembra to run a job
    """
    url = "https://api.zembra.io/reviews/job/google"
    payload = f"slug={self.cid}&includeRawData=true&streamSizeLimit={limit}&fields[]=id&fields[]=text&fields[]=rating&fields[]=author"
    headers = {
        'Accept': "application/json, application/json, application/json, application/json, application/json, application/json",
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache",
        'Authorization': f"Bearer {API_KEY}"
    }

    response = requests.request("POST", url, data=payload, headers=headers).json()
    if response['status'] == "SUCCESS":
      return response['data']['job']['jobId']
    else:
      raise FailedHTTPResponse()

  def __get_request_data(self, id):
    """
      Get the data of the request if avaliable, else return False
    """
    url = f"https://api.zembra.io/reviews/job/{id}"
    headers = {
        'Accept': "application/json, application/json, application/json, application/json, application/json, application/json",
        'Cache-Control': "no-cache",
        'Authorization': f"Bearer {API_KEY}"
    }

    response = requests.get(url, headers=headers).json()
    if "in progress" in response['message']:
      return False
    
    else: 
      return response['data']['reviews']


  def fetch_reviews(self, limit = 100):
    """
      Send a request for review data and wait until data is returned
    """
    jobId = self.__send_review_request(limit)

    response = self.__get_request_data(jobId)

    while not response:
      time.sleep(2)
      response = self.__get_request_data(jobId)
    
    self.reviews = response

  def process_review_data(self):
    """
      Read response data and process into parseable, normalized data with only the fields necessary
    """
    self.reviews = [unidecode.unidecode(x['text']).replace("\n", " ") for x in self.reviews if x['text']]

  def analyze_reviews(self, reviews):
    """
     Use OpenAI davinci003 @ 0.91 temp to analyze and extract sentiment and foods
    """
    response = openai.Completion.create(
      model="text-davinci-003",
      prompt="Name the specific dishes mentioned in the following reviews and determine if the review is positive or negative about each dish. \n\nReturn as a JSON response in format:\n\n[{\"name\": <dish name>, \"pos\": <number of positive reviews>, \"neg\": <number of negative reviews> }]\n\nReviews: \n\n" + "\n\n".join(reviews) + "\n\nResponse:",
      temperature=0.32,
      max_tokens=512,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    return json.loads(response['choices'][0]['text'])

  def vectorize(self, text):
    """
      Return w2v vector
    """
    def preprocess(s):
      return [i.lower() for i in s.split()]

    def get_vector(s):
      return np.sum(np.array([self.w2v[i] for i in preprocess(s)]), axis=0)

    return get_vector(text)

  def extract_all_dishes(self):
    """
        Extract all dishes from all reviews and aggregate them into a single list of dishes in format:
        {<dish name>: {pos: <number of positive reviews>, neg: <number of negative reviews> } }
        TODO: parallize with sephamores + thread queue 
    """
    def chunk_r(lst, n):
      for p in range(0, len(lst), n):
        yield lst[p:p+n]

    all_foods = {}

    tp = ThreadPoolExecutor(max_workers=10)
    tp_results = [tp.submit(self.analyze_reviews, chunk) for chunk in chunk_r(self.reviews, 6)]
    
    for chunk in tp_results:
      for z in chunk.result():
        lowered_name = z['name'].lower()
        if lowered_name in all_foods:
          all_foods[lowered_name]['pos'] += z['pos']
          all_foods[lowered_name]['neg'] += z['neg']
          all_foods[lowered_name]['agg'] += z['pos'] - z['neg']
        else:
          all_foods[lowered_name] = {}
          all_foods[lowered_name]['pos'] = z['pos']
          all_foods[lowered_name]['neg'] = z['neg']
          all_foods[lowered_name]['agg'] = z['pos'] - z['neg']

    # drop keys we don't want
    for p in ['ambiance', 'food', 'service', 'drinks', "menu", "dishes", "cocktails", "meal", "location", "atmosphere", "wine", "meals"]:
      all_foods.pop(p, None)

    return all_foods
    
  def merge_items(self, lst):
    """
      Merge similiar food items, as defined by cos sim > 0.8
    """
    computed_vectors = {}
    final_rankings = {}
    added_keys = []

    for entree, ratings in lst.items():
      try:
        ratings['vec'] = self.vectorize(entree)
        computed_vectors[entree] = ratings
      except:
        # unknown vector -> results in partial computation
        pass
        # final_rankings[entree] = ratings
        # final_rankings[entree]["matches"] = [] 
    
    cv_list = sorted(list(computed_vectors.items()), key=lambda x: len(x[0]))
    # to do: sort by length, so broadest/shortest goes first. 
    for name, rate_vec in cv_list:
      if name in added_keys: # if already added to matched list, skip
        continue

      matches = []
      
      # iterate through the remaining items in the dictionary
      for name2, rate_vec2 in cv_list[list(computed_vectors).index(name)+1:]:
          if 1 - spatial.distance.cosine(rate_vec["vec"], rate_vec2["vec"]) > 0.8 and name2 != name:
              matches.append(name2)
              added_keys.append(name2)
              rate_vec = {k: rate_vec.get(k, 0) + rate_vec2.get(k, 0) for k in set(rate_vec)}
              # del computed_vectors[name2] # remove the matched item from the dictionary
      
      final_rankings[name] = rate_vec
      final_rankings[name]["matches"] = matches 
      
    return final_rankings

  def return_rankings(self):
    """
      return data extraction + merge + ranking
    """
    if not hasattr(self, "extracted_data"): # cache results
      self.extracted_data = self.extract_all_dishes()
    
    unsorted_merge = self.merge_items(self.extracted_data)

    return sorted(unsorted_merge.items(), key=lambda x: x[1]['agg'])
