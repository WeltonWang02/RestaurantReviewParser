# RestaurantReviewParaser

Extension of BetterFoodRecs

*Given restaurant A, find the most positively reviewed items on the menu*

## Requirements

- OpenAI API Key
- Zembra API Key

## Setup

Pre-requisites

```bash
pip3 install unidecode openai gdown gensim Sanic python-dotenv
gdown https://drive.google.com/uc?id=0B7XkCwpI5KDYNlNUTTlSS21pQmM
gzip -d GoogleNews-vectors-negative300.bin.gz
```

Create a `.env` file with:

```
REVIEW_COUNT=400 # number of reviews to analyze
PORT=8085 # port to run server on
OPENAI_API=API_KEY # openai api key
ZEMBRA_API=API_KEY # zembra api key
```

To start:

```python3 app.py```

## Usage

```Method: POST 
Endpoint: /api/v1/fetch/
Body: {"location": "<location slug>"}

<location slug> = Google Maps location ID. Formats:
472717649119152494
https://www.google.com/maps?cid=472717649119152494
https://maps.google.com/maps?cid=472717649119152494
ChIJx0JMBTFV2YARbgnOgjJujwY
https://www.google.com/maps/place/The+Cheesecake+Factory/@32.76918,-117.1677887,17z/data=!3m1!4b1!4m5!3m4!1s0x0:0x68f6e3282ce096e!8m2!3d32.76918!4d-117.1656
0x68f6e3282ce096e
```

## Cost

Zembra API Cost: $0.06 + $0.12/100 reviews

OpenAI API Cost: ~ $0.14/100 reviews

Total Cost/Request (400 review default): ~$1

*Reducing costs: Instead of text-davinci-003, a lower-powered GPT model can be used to lower review parsing costs.* 
