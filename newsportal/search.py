from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from news.models import Article


def fulltext_search_articles(term, category_slug=None):
    vector = (
        SearchVector("title", weight="A")
        + SearchVector("summary", weight="B")
        + SearchVector("content", weight="C")
    )

    query = SearchQuery(term)
    qs = Article.objects.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.1)
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    return qs.order_by("-rank", "-published_at")
