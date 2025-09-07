import graphene
from graphql import GraphQLError
from django.utils import timezone
from django.db import transaction
from taggit.models import Tag
from news.models import Article, Comment
from users.models import User
from categories.models import Category
from .types import ArticleType, CommentType, UserType


# Permission helpers
def require_auth(info):
    user = info.context.user
    if not user.is_authenticated:
        raise GraphQLError("Authentication required")
    return user


def require_role(user, roles):
    if user.role not in roles:
        raise GraphQLError("You don't have permission to perform this action")


# Article mutations
class CreateArticle(graphene.Mutation):
    article = graphene.Field(ArticleType)

    class Arguments:
        title = graphene.String(required=True)
        summary = graphene.String(required=True)
        content = graphene.String(required=True)
        category_id = graphene.ID(required=True)
        tag_ids = graphene.List(graphene.ID)
        status = graphene.String()
        is_featured = graphene.Boolean()

        @transaction.atomic
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
            user = require_auth(info)
            require_role(user, ["journalist", "editor"])
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                raise GraphQLError("Category not found")
            article = Article.objects.create(
                title=title,
                summary=summary,
                content=content,
                category=category,
                author=user,
                status=status,
                is_featured=is_featured,
                published_at=timezone.now() if status == "published" else None,
            )
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
        category_id = graphene.String()
        tag_ids = graphene.List(graphene.ID)
        is_featured = graphene.Boolean()
        status = graphene.String()

    @transaction.atomic
    def mutate(
        self,
        info,
        id,
        title=None,
        content=None,
        summary=None,
        category_id=None,
        tag_ids=None,
        is_featured=None,
        status=None,
    ):
        type_name, db_id = graphene.relay.Node.from_global_id(id)

        if type_name != "ArticleType":
            raise GraphQLError("Invalid ID type")

        user = require_auth(info)
        try:
            article = Article.objects.get(pk=db_id)
        except Article.DoesNotExist:
            raise GraphQLError("Article not found")
        if user != article.author and user.role != "editor":
            raise GraphQLError("Only the author or an editor can update this article")

        if title is not None:
            article.title = title
        if summary is not None:
            article.summary = summary
        if content is not None:
            article.content = content
        if category_id is not None:
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                raise GraphQLError("Category not found")
            article.category = category
        if status is not None:
            article.status = status
            if status == "published" and article.published_at is None:
                article.published_at = timezone.now()
        if is_featured is not None:
            article.is_featured = is_featured
        article.save()

        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids)
            article.tags.set(tags)

        return UpdateArticle(article=article)


class DeleteArticle(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        type_name, db_id = graphene.relay.Node.from_global_id(id)

        if type_name != "ArticleType":
            raise GraphQLError("Invalid ID type")

        user = require_auth(info)
        try:
            article = Article.objects.get(pk=id)
        except Article.DoesNotExist:
            raise GraphQLError("Article not found")
        if user != article.author and user.role != "editor":
            raise GraphQLError("Only the author or an editor can delete this article")

        article.delete()
        return DeleteArticle(success=True)


# Comment mutation
class AddComment(graphene.Mutation):
    comment = graphene.Field(CommentType)

    class Arguments:
        article_id = graphene.ID(required=True)
        text = graphene.String(required=True)

    def mutate(self, info, article_id, content):
        user = require_auth(info)
        try:
            article = Article.objects.get(pk=article_id)
        except Article.DoesNotExist:
            raise GraphQLError("Article not found or not published")
        comment = Comment.objects.create(article=article, user=user, content=content)

        from .subscriptions import comment_broadcast

        comment_broadcast(comment)
        return AddComment(comment=comment)


class DeleteComment(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        user = require_auth(info)
        try:
            comment = Comment.objects.get(pk=id)
        except Comment.DoesNotExist:
            raise GraphQLError("Comment not found")

        if comment.user != user and user.role != "editor":
            raise GraphQLError("Only the author or an editor can delete this comment")
        comment.delete()
        return DeleteComment(success=True)


# User mutations
class Signup(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        role = graphene.String(required=False)
        bio = graphene.String(required=False)

    user = graphene.Field(UserType)

    def mutate(self, info, username, password, role="reader", bio=""):
        if User.objects.filter(username=username).exists():
            raise GraphQLError("Username already taken")
        user = User.objects.create_user(
            username=username, password=password, role=role, bio=bio
        )
        return Signup(user=user)


class UpdateProfile(graphene.Mutation):
    class Arguments:
        first_name = graphene.String()
        last_name = graphene.String()
        bio = graphene.String()

    user = graphene.Field(UserType)

    def mutate(self, info, first_name=None, last_name=None, bio=None):
        user = require_auth(info)
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if bio is not None:
            user.bio = bio
        user.save()
        return UpdateProfile(user=user)


class Mutation(graphene.ObjectType):
    create_article = CreateArticle.Field()
    update_article = UpdateArticle.Field()
    delete_article = DeleteArticle.Field()

    add_comment = AddComment.Field()
    delete_comment = DeleteComment.Field()

    signup = Signup.Field()
    update_profile = UpdateProfile.Field()

    # JWT helpers
    from graphql_jwt.shortcuts import get_token
    import graphql_jwt

    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
