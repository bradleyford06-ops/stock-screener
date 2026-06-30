import requests
import logging

logger = logging.getLogger(__name__)

_sentiment_pipeline = None


def get_sentiment_pipeline():
    """Load FinBERT sentiment model once and reuse it (model is ~400MB, slow first load)."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline
        logger.info("Loading FinBERT sentiment model (first run may take a minute)...")
        _sentiment_pipeline = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT model loaded.")
    return _sentiment_pipeline


def fetch_news_headlines(company_name, symbol, max_results=5):
    """Fetch recent news headlines for a stock using Yahoo Finance's built-in news feed."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if not news:
            return []
        headlines = []
        for item in news[:max_results]:
            title = item.get("content", {}).get("title") or item.get("title", "")
            if title:
                headlines.append(title)
        return headlines
    except Exception as e:
        logger.warning(f"News fetch failed for {symbol}: {e}")
        return []


def score_sentiment(symbol, company_name):
    """Fetch headlines and run FinBERT on them. Returns sentiment score from -1.0 to 1.0."""
    headlines = fetch_news_headlines(company_name, symbol)
    if not headlines:
        return 0.0, []

    try:
        pipe = get_sentiment_pipeline()
        scores = []
        for headline in headlines:
            result = pipe(headline)[0]
            label = result["label"].lower()
            conf = result["score"]
            if label == "positive":
                scores.append(conf)
            elif label == "negative":
                scores.append(-conf)
            else:
                scores.append(0.0)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        return round(avg_score, 3), headlines

    except Exception as e:
        logger.warning(f"FinBERT scoring failed for {symbol}: {e}")
        return 0.0, headlines
