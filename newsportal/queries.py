import graphene
from django.db.models import Q
from django.utils import timezone
from graphql import GraphQLError
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import (
    login_required,
)
from news.models import Article, Bookmark, Comment, Tag
from categories.models import Category
from .types import (
    ArticleType,
    BookmarkType,
    CategoryType,
    CommentType,
    LikeType,
    UserType,
    TagType,
)
from users.models import User


class Query(graphene.ObjectType):
    # Node field for relay
    node = graphene.relay.Node.Field()

    # User queries
    users = DjangoFilterConnectionField(UserType)
    user = graphene.Field(
        UserType,
        id=graphene.ID(),
        username=graphene.String(),
    )
    me = graphene.Field(UserType)

    # Category queries
    categories = DjangoFilterConnectionField(CategoryType)
    category = graphene.Field(
        CategoryType,
        id=graphene.ID(),
        slug=graphene.String(),
    )

    # Tag queries
    tags = DjangoFilterConnectionField(TagType)
    tag = graphene.Field(
        TagType,
        id=graphene.ID(),
        slug=graphene.String(),
    )

    # Article queries
    articles = DjangoFilterConnectionField(
        ArticleType,
        search=graphene.String(),
        category_slug=graphene.String(),
        tag=graphene.String(),
        status=graphene.String(),
        order_by=graphene.String(),
    )
    article = graphene.Field(ArticleType, id=graphene.ID(), slug=graphene.String())
    featured_articles = graphene.List(ArticleType)
    recent_articles = graphene.List(ArticleType, limit=graphene.Int(required=True))
    popular_articles = graphene.List(ArticleType, limit=graphene.Int())
    articles_by_category = graphene.List(ArticleType, category_id=graphene.ID())
    articles_by_tag = graphene.List(ArticleType, tag_id=graphene.ID())
    search_articles = graphene.List(ArticleType, graphene.String(required=True))

    # Comment queries
    comments = DjangoFilterConnectionField(CommentType)
    comment = graphene.Field(CommentType, id=graphene.ID())
    comments_by_article = graphene.List(
        CommentType, article_id=graphene.ID(required=True)
    )

    # Like and Bookmark queries
    likes = DjangoFilterConnectionField(LikeType)
    bookmarks = DjangoFilterConnectionField(BookmarkType)
    user_bookmarks = graphene.List(BookmarkType)

    # Resolvers
    def resolve_user(self, info, id=None, username=None):
        if id:
            type_name, db_id = graphene.relay.Node.from_global_id(id)
            if type_name != "UserType":
                raise GraphQLError("Invalid ID type")
            return User.objects.get(pk=db_id)
        if username:
            return User.objects.get(username=username)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    def resolve_category(self, info, id=None, slug=None):
        if id:
            type_name, db_id = graphene.relay.Node.from_global_id(id)
            if type_name != "CategoryType":
                raise GraphQLError("Invalid ID type")
            return Category.objects.get(pk=db_id)
        if slug:
            return Category.objects.get(slug=slug)
        return None

    def resolve_tag(self, info, id=None, slug=None):
        if id:
            type_name, db_id = graphene.relay.Node.from_global_id(id)
            if type_name != "TagType":
                raise GraphQLError("Invalid ID type")
            return Tag.objects.get(pk=db_id)
        if slug:
            return Tag.objects.get(slug=slug)
        return None

    def resolve_articles(
        self,
        info,
        search=None,
        category_slug=None,
        tag=None,
        status="published",
        order_by="-published_at",
        **kwargs
    ):
        qs = Article.objects.select_related("author", "category").prefetch_related(
            "tags", "comments"
        )
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(summary__icontains=search)
                | Q(content__icontains=search)
            )
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        if tag:
            qs = qs.filter(tags__slug=tag)

        if status:
            qs = qs.filter(status=status)

        if order_by:
            qs = qs.order_by(order_by)

        return qs

    def resolve_article(self, info, id=None, slug=None):
        if id:
            type_name, db_id = graphene.relay.Node.from_global_id(id)
            if type_name != "ArticleType":
                raise GraphQLError("Invalid ID type")
            return (
                Article.objects.select_related("author", "category")
                .prefetch_related("tags", "comments")
                .get(pk=db_id)
            )
        if slug:
            return (
                Article.objects.select_related("author", "category")
                .prefetch_related("tags", "comments")
                .get(slug=slug)
            )
        return None

    def resolve_featured_articles(self, info):
        return Article.objects.filter(is_featured=True, status="published")

    def resolve_recent_articles(self, info, limit):
        return Article.objects.filter(status="published").order_by("-published_at")[
            :limit
        ]

    def resolve_popular_articles(self, info, limit=10):
        return Article.objects.filter(status="published").order_by("-views_count")[
            :limit
        ]

    def resolve_articles_by_category(self, info, category_id):
        db_id = graphene.relay.Node.from_global_id(category_id)[1]
        return Article.objects.filter(category_id=db_id, status="published")

    def resolve_articles_by_tag(self, info, tag_id):
        db_id = graphene.relay.Node.from_global_id(tag_id)[1]
        return Article.objects.filter(tags__id=db_id, status="published")

    def resolve_search_articles(self, info, query):
        return Article.objects.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query),
            status="published",
        )

    def resolve_comment(self, info, id):
        if id:
            db_id = graphene.relay.Node.from_global_id(id)[1]
            return Comment.objects.get(pk=db_id)

    def resolve_comments_by_article(self, info, article_id):
        if article_id:
            db_id = graphene.relay.Node.from_global_id(article_id)
            return Comment.objects.filter(article_id=db_id, is_approved=True)

    @login_required
    def resolve_user_bookmarks(self, info):
        return Bookmark.objects.filter(user=info.context.user)
