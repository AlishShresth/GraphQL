from django.db.models import Q
import graphene
import graphql_jwt
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import (
    login_required,
    staff_member_required,
    superuser_required,
)
from users.models import User
from categories.models import Category
from news.models import Tag, Article, Comment, Like, Bookmark


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = "__all__"
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
        fields = "__all__"
        filter_fields = {
            "id": ["exact"],
            "name": ["exact", "icontains"],
            "slug": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = "__all__"
        filter_fields = {
            "id": ["exact"],
            "name": ["exact", "icontains"],
            "slug": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = "__all__"
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
        fields = "__all__"
        filter_fields = {
            "id": ["exact"],
            "article": ["exact"],
            "user": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class BookmarkType(DjangoObjectType):
    class Meta:
        model = Bookmark
        fields = "__all__"
        filter_fields = {
            "id": ["exact"],
            "article": ["exact"],
            "user": ["exact"],
        }
        interfaces = (graphene.relay.Node,)


class ArticleType(DjangoObjectType):
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    is_liked = graphene.Boolean()
    is_bookmarked = graphene.Boolean()

    class Meta:
        model = Article
        fields = "__all__"
        filter_fields = {
            "id": ["exact"],
            "title": ["exact", "icontains"],
            "slug": ["exact"],
            "status": ["exact"],
            "is_featured": ["exact"],
            "author": ["exact"],
            "category": ["exact"],
            "tags": ["exact"],
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


# Query Class
class Query(graphene.ObjectType):
    # Node fields for relay
    node = graphene.relay.Node.Field()

    # User queries
    users = DjangoFilterConnectionField(UserType)
    user = graphene.Field(
        UserType,
        id=graphene.Int(),
        username=graphene.String(),
    )
    me = graphene.Field(UserType)

    # Category queries
    categories = DjangoFilterConnectionField(CategoryType)
    category = graphene.Field(
        CategoryType,
        id=graphene.Int(),
        slug=graphene.String(),
    )

    # Tag queries
    tags = DjangoFilterConnectionField(TagType)
    tag = graphene.Field(
        TagType,
        id=graphene.Int(),
        slug=graphene.String(),
    )

    # Article queries
    articles = DjangoFilterConnectionField(ArticleType)
    article = graphene.Field(ArticleType, id=graphene.Int(), slug=graphene.String())
    featured_articles = graphene.List(ArticleType)
    recent_articles = graphene.List(ArticleType, limit=graphene.Int())
    popular_articles = graphene.List(ArticleType, limit=graphene.Int())
    articles_by_category = graphene.List(ArticleType, category_slug=graphene.String())
    articles_by_tag = graphene.List(ArticleType, tag_slug=graphene.String())
    search_articles = graphene.List(ArticleType, query=graphene.String())

    # Comment queries
    comments = DjangoFilterConnectionField(CommentType)
    comment = graphene.Field(CommentType, id=graphene.Int())
    comments_by_article = graphene.List(CommentType, article_id=graphene.Int())

    # Like and Bookmark queries
    likes = DjangoFilterConnectionField(LikeType)
    bookmarks = DjangoFilterConnectionField(BookmarkType)
    user_bookmarks = graphene.List(BookmarkType)

    def resolve_user(self, info, id=None, username=None):
        if id:
            return User.objects.get(pk=id)
        if username:
            return User.objects.get(username=username)
        return None

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    def resolve_category(self, info, id=None, slug=None):
        if id:
            return Category.objects.get(pk=id)
        if slug:
            return Category.objects.get(slug=slug)
        return None

    def resolve_tag(self, info, id=None, slug=None):
        if id:
            return Tag.objects.get(pk=id)
        if slug:
            return Tag.objects.get(slug=slug)
        return None

    def resolve_article(self, info, id=None, slug=None):
        if id:
            return Article.objects.get(pk=id)
        if slug:
            return Article.objects.get(slug=slug)
        return None

    def resolve_featured_articles(self, info):
        return Article.objects.filter(is_featured=True, status="published")

    def resolve_recent_articles(self, info, limit=None):
        limit = limit or 10
        return Article.objects.filter(status="published").order_by("-published_at")[
            :limit
        ]

    def resolve_popular_articles(self, info, limit=None):
        limit = limit or 10
        return Article.objects.filter(status="published").order_by("-views_count")[
            :limit
        ]

    def resolve_articles_by_category(self, info, category_slug):
        try:
            category = Category.objects.get(slug=category_slug)
            return Article.objects.filter(category=category, status="published")
        except Category.DoesNotExist:
            return []

    def resolve_articles_by_tag(self, info, tag_slug):
        try:
            tag = Tag.objects.get(slug=tag_slug)
            return Article.objects.filter(tags=tag, status="published")
        except Tag.DoesNotExist:
            return []

    def resolve_search_articles(self, info, query):
        if not query:
            return []

        return Article.objects.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query),
            status="published",
        )

    def resolve_comment(self, info, id):
        return Comment.objects.get(pk=id)

    def resolve_comments_by_article(self, info, article_id):
        return Comment.objects.filter(article_id=article_id, is_approved=True)

    def resolve_user_bookmarks(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Bookmark.objects.filter(user=user)
        return []


# Mutation Class
class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()

    def mutate(self, info, username, email, password, first_name=None, last_name=None):
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save()

        return CreateUser(user=user)


class UpdateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        id = graphene.ID(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        bio = graphene.String()
        website = graphene.String()
        twitter = graphene.String()
        facebook = graphene.String()
        instagram = graphene.String()

    def mutate(
        self,
        info,
        id,
        first_name=None,
        last_name=None,
        bio=None,
        website=None,
        twitter=None,
        facebook=None,
        instagram=None,
    ):
        user = User.objects.get(pk=id)

        # check if the user is updating their own profile or is an editor
        if info.context.user != user and not info.context.user.is_editor:
            raise Exception("You don't have permission to update this user")

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if bio is not None:
            user.bio = bio
        if website is not None:
            user.website = website
        if twitter is not None:
            user.twitter = twitter
        if facebook is not None:
            user.facebook = facebook
        if instagram is not None:
            user.instagram = instagram

        user.save()
        return UpdateUser(user=user)


class CreateCategory(graphene.Mutation):
    category = graphene.Field(CategoryType)

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        parent_id = graphene.ID()

    def mutate(self, info, name, description=None, parent_id=None):
        # Only editors can create categories
        if not info.context.user.is_authenticated or not info.context.user.is_editor:
            raise Exception("You don't have permission to create categories")

        parent = None
        if parent_id:
            parent = Category.objects.get(pk=parent_id)

        category = Category(name=name, description=description, parent=parent)
        category.save()

        return CreateCategory(category=category)


class UpdateCategory(graphene.Mutation):
    category = graphene.Field(CategoryType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        parent_id = graphene.ID()

    def mutate(self, info, id, name=None, description=None, parent_id=None):
        # Only editors can update categories
        if not info.context.user.is_authenticated or not info.context.user.is_editor:
            raise Exception("You don't have permissions to update categories")

        category = Category.objects.get(pk=id)

        if name is not None:
            category.name = name
        if description is not None:
            category.description = description

        parent = None
        if parent_id:
            parent = Category.objects.get(pk=parent_id)
        category.parent = parent

        category.save()
        return UpdateCategory(category=category)


class DeleteCategory(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    def mutate(self, info, id):
        # Only editors can delete categories
        if not info.context.user.is_authenticated or not info.context.user.is_editor:
            raise Exception("You don't have permission to delete categories")

        try:
            category = Category.objects.get(pk=id)
            category.delete()
            return DeleteCategory(success=True)
        except Category.DoesNotExist:
            return DeleteCategory(success=False)


class CreateTag(graphene.Mutation):
    tag = graphene.Field(TagType)

    class Arguments:
        name = graphene.String(required=True)

    def mutate(self, info, name):
        # Only journalists and editors can create tags
        if not info.context.user.is_authenticated or not (
            info.context.user.is_journalist or info.context.user.is_editor
        ):
            raise Exception("You don't have the permission to create tags")

        tag = Tag(name=name)
        tag.save()

        return CreateTag(tag=tag)


class CreateArticle(graphene.Mutation):
    article = graphene.Field(ArticleType)

    class Arguments:
        title = graphene.String(required=True)
        summary = graphene.String(required=True)
        content = graphene.String(required=True)
        category_id = graphene.ID(required=True)
        tag_ids = graphene.List(graphene.ID)
        is_featured = graphene.Boolean()
        status = graphene.String()

    def mutate(
        self,
        info,
        title,
        summary,
        content,
        category_id,
        tag_ids=None,
        is_featured=False,
        status="draft",
    ):
        # Only journalists and editors can create articles
        if not info.context.user.is_authenticated:
            raise Exception("You must be logged in to create articles")

        if not (info.context.user.is_journalist or info.context.user.is_editor):
            raise Exception("You don't have permission to create articles")

        category = Category.objects.get(pk=category_id)

        article = Article(
            title=title,
            summary=summary,
            content=content,
            author=info.context.user,
            category=category,
            is_featured=is_featured,
            status=status,
        )
        article.save()

        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            article.tags.set(tags)

        return CreateArticle(article=article)


class UpdateArticle(graphene.Mutation):
    article = graphene.Field(ArticleType)

    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String()
        summary = graphene.String()
        content = graphene.String()
        category_id = graphene.ID()
        tag_ids = graphene.List(graphene.ID)
        is_featured = graphene.Boolean()
        status = graphene.String()

    def mutate(
        self,
        info,
        id,
        title=None,
        summary=None,
        content=None,
        category_id=None,
        tag_ids=None,
        is_featured=False,
        status=None,
    ):
        # Only journalists and editors can create articles
        if not info.context.user.is_authenticated or not (
            info.context.user.is_journalist or info.context.user.is_editor
        ):
            raise Exception("You don't have permission to create articles")

        article = Article.objects.get(pk=id)

        if title is not None:
            article.title = title
        if summary is not None:
            article.summary = summary
        if content is not None:
            article.content = content
        if category_id is not None:
            article.category_id = category_id
        if is_featured is not None:
            article.is_featured = is_featured
        if status is not None:
            article.status = status

        article.save()

        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids)
            article.tags.set(tags)

        return UpdateArticle(article=article)


class DeleteArticle(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    def mutate(self, info, id):
        article = Article.objects.get(pk=id)

        # Check if the user is the author or an editor
        if not info.context.user.is_authenticated or (
            info.context.user != article.author and not info.context.user.is_editor
        ):
            raise Exception("You don't have permission to create articles")

        article.delete()
        return DeleteArticle(success=True)


class CreateComment(graphene.Mutation):
    comment = graphene.Field(CommentType)

    class Arguments:
        article_id = graphene.ID(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.ID()

    def mutate(self, info, article_id, content, parent_id=None):
        # Only authenticated users can create comments
        if not info.context.user.is_authenticated:
            raise Exception("You must be logged in to comment")

        article = Article.objects.get(pk=article_id)
        parent = None
        if parent_id:
            parent = Comment.objects.get(pk=parent_id)

        comment = Comment(
            article=article, user=info.context.user, content=content, parent=parent
        )
        comment.save()

        return CreateComment(comment=comment)


class DeleteComment(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    def mutate(self, info, id):
        comment = Comment.objects.get(pk=id)

        # Check if the user is the comment author or an editor
        if info.context.user != comment.user and not info.context.user.is_editor:
            raise Exception("You don't have permission to delete this comment")

        comment.delete()
        return DeleteComment(success=True)


class LikeArticle(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        article_id = graphene.ID(required=True)

    def mutate(self, info, article_id):
        # only authenticated users can like articles
        if not info.context.user.is_authenticated:
            raise Exception("You must be logged in to like articles")

        article = Article.objects.get(pk=article_id)
        user = info.context.user

        like, created = Like.objects.get_or_create(article=article, user=user)

        if not created:
            # If like already exists, remove
            like.delete()
            return LikeArticle(success=False)

        return LikeArticle(success=True)


class BookmarkArticle(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        article_id = graphene.ID(required=True)

    def mutate(self, info, article_id):
        # Only authenticated users can bookmark articles
        if not info.context.user.is_authenticated:
            raise Exception("You must be logged in to bookmark articles")

        article = Article.objects.get(pk=article_id)
        user = info.context.user

        bookmark, created = Bookmark.objects.get_or_create(article=article, user=user)

        if not created:
            # if bookmark already exists, remove
            bookmark.delete()
            return BookmarkArticle(success=False)

        return BookmarkArticle(success=True)


class Mutation(graphene.ObjectType):
    # User mutations
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()

    # Category mutations
    create_category = CreateCategory.Field()
    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()

    # Tag mutations
    create_tag = CreateTag.Field()

    # Article mutations
    create_article = CreateArticle.Field()
    update_article = UpdateArticle.Field()
    delete_article = DeleteArticle.Field()

    # Comment mutations
    create_comment = CreateComment.Field()
    delete_comment = DeleteComment.Field()

    # Like and Bookmark mutations
    like_article = LikeArticle.Field()
    bookmark_article = BookmarkArticle.Field()

    # JWT mutations
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
