import graphene
from graphene_django import DjangoObjectType
from users.models import User
from news.models import Article, Comment, Tag, Like, Bookmark
from categories.models import Category


class RoleEnum(graphene.Enum):
    READER = "reader"
    JOURNALIST = "journalist"
    EDITOR = "editor"


class UserType(DjangoObjectType):
    role = RoleEnum()
    is_journalist = graphene.Boolean(source="is_journalist")
    is_editor = graphene.Boolean(source="is_editor")
    is_reader = graphene.Boolean(source="is_reader")

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "bio",
            "website",
            "twitter",
            "facebook",
            "instagram",
            "profile_image",
            "date_joined",
            "updated_at",
        )
        filter_fields = {
            "id": ["exact"],
            "username": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "role": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class CategoryType(DjangoObjectType):
    is_subcategory = graphene.Boolean(source="is_subcategory")
    main_category = graphene.Field(lambda: CategoryType, source="get_main_category")

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "parent",
            "children",
            "created_at",
            "updated_at",
        )
        filter_fields = {
            "id": ["exact"],
            "name": ["exact", "icontains"],
            "slug": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug", "created_at")
        filter_fields = {
            "id": ["exact"],
            "name": ["exact", "icontains"],
            "slug": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class ArticleType(DjangoObjectType):
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    is_liked = graphene.Boolean()
    is_bookmarked = graphene.Boolean()

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "slug",
            "summary",
            "content",
            "featured_image",
            "author",
            "category",
            "tags",
            "status",
            "is_featured",
            "views_count",
            "created_at",
            "updated_at",
            "published_at",
            "comments"
        )
        filter_fields = {
            "id": ["exact"],
            "title": ["exact", "icontains"],
            "slug": ["exact"],
            "status": ["exact"],
            "is_featured": ["exact"],
            "author__id": ["exact"],
            "author__username": ["exact", "icontains"],
            "category__id": ["exact"],
            "category__name": ["exact", "icontains"],
            "category__slug": ["exact"],
            "tags__id": ["exact"],
            "tags__name": ["exact", "icontains"],
            "tags__slug": ["exact"],
            "published_at": ["exact", "lt", "gt", "lte", "gte"],
        }
        interfaces = (graphene.relay.Node,)

    def resolve_likes_count(self, info):
        return self.likes.count()

    def resolve_comments_count(self, info):
        return self.comments.count()

    def resolve_is_liked(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Like.objects.filter(article=self, user=user).exists()
        return False

    def resolve_is_bookmarked(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Bookmark.objects.filter(article=self, user=user).exists()
        return False


class CommentType(DjangoObjectType):
    children = graphene.Field(lambda: CommentType, source="children")

    class Meta:
        model = Comment
        fields = (
            "id",
            "article",
            "user",
            "content",
            "parent",
            "is_approved",
            "created_at",
            "updated_at",
        )
        filter_fields = {
            "id": ["exact"],
            "article": ["exact"],
            "user": ["exact"],
            "is_approved": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class LikeType(DjangoObjectType):
    class Meta:
        model = Like
        fields = ("id", "article", "user", "created_at")
        filter_fields = {
            "id": ["exact"],
            "article": ["exact"],
            "user": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class BookmarkType(DjangoObjectType):
    class Meta:
        model = Bookmark
        fields = ("id", "article", "user", "created_at")
        filter_fields = {
            "id": ["exact"],
            "article": ["exact"],
            "user": ["exact"],
        }
        interfaces = (graphene.relay.Node,)
