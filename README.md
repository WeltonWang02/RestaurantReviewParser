# RestaurantReviewParaser

Extension of BetterFoodRecs

*Given restaurant A, find the most positively reviewed items on the menu*

## Requirements

- OpenAI API Key
- Zembra API Key

## Setup

Pre-requisites

```bash
pip3 install unidecode openai gdown
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

## Cost

Zembra API Cost: $0.06 + $0.12/100 reviews
OpenAI API Cost: ~ $0.14/100 reviews
Total Cost/Request (400 review default): ~$1

*Reducing costs: Instead of text-davinci-003, a lower-powered GPT model can be used to lower review parsing costs.* 
