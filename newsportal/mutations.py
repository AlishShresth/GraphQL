import graphene
from graphql import GraphQLError
from graphene.relay.node import from_global_id
from django.utils import timezone
from django.db import transaction, IntegrityError
from taggit.models import Tag
from news.models import Article, Bookmark, Comment, Like
from users.models import User
from categories.models import Category
from .types import ArticleType, CategoryType, CommentType, TagType, UserType


# Permission helpers
def require_auth(info):
    user = info.context.user
    if not user.is_authenticated:
        raise GraphQLError("You need to be logged in to perform this action")
    return user


def require_role(user, roles):
    if user.role not in roles:
        raise GraphQLError("You don't have permission to perform this action")


def get_object_or_error(model, db_id, not_found_msg):
    try:
        return model.objects.get(pk=db_id)
    except model.DoesNotExist:
        raise GraphQLError(not_found_msg)


# User mutations
class Signup(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        role = graphene.String(required=False)
        bio = graphene.String(required=False)

    user = graphene.Field(UserType)

    def mutate(
        self,
        info,
        username,
        email,
        password,
        first_name=None,
        last_name=None,
        role="reader",
        bio="",
    ):
        if User.objects.filter(username=username).exists():
            raise GraphQLError("Username already taken")
        if User.objects.filter(email=email).exists():
            raise GraphQLError("Email already taken")
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            bio=bio,
        )
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            raise GraphQLError("A user with this username/email already exists")

        return Signup(user=user)


class UpdateProfile(graphene.Mutation):
    class Arguments:
        first_name = graphene.String()
        last_name = graphene.String()
        bio = graphene.String()
        website = graphene.String()
        twitter = graphene.String()
        facebook = graphene.String()
        instagram = graphene.String()

    user = graphene.Field(UserType)

    def mutate(
        self,
        info,
        first_name=None,
        last_name=None,
        bio=None,
        website=None,
        twitter=None,
        facebook=None,
        instagram=None,
    ):
        user = require_auth(info)
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
        return UpdateProfile(user=user)


# Category mutations
class CreateCategory(graphene.Mutation):
    category = graphene.Field(CategoryType)

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        parent_id = graphene.ID()

    def mutate(self, info, name, description=None, parent_id=None):
        user = require_auth(info)
        require_role(user, ["editor"])

        parent = None
        if parent_id:
            type_name, db_id = from_global_id(parent_id)
            if type_name != "CategoryType":
                raise GraphQLError("Invalid ID type")
            parent = Category.objects.get(pk=db_id)

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
        user = require_auth(info)
        require_role(user, ["editor"])

        type_name, db_id = from_global_id(id)
        if type_name != "CategoryType":
            raise GraphQLError("Invalid ID type")

        try:
            category = Category.objects.get(pk=db_id)
        except Category.DoesNotExist:
            raise GraphQLError("Category not found")

        if name is not None:
            category.name = name
        if description is not None:
            category.description = description

        if parent_id is not None:
            type_name, db_id = from_global_id(parent_id)
            if type_name != "CategoryType":
                raise GraphQLError("Invalid ID type")

            try:
                parent = Category.objects.get(pk=db_id)
            except Category.DoesNotExist:
                raise GraphQLError("Parent category not found")

            category.parent = parent

        category.save()
        return UpdateCategory(category=category)


class DeleteCategory(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    def mutate(self, info, id):
        user = require_auth(info)
        require_role(user, ["editor"])

        type_name, db_id = from_global_id(id)
        if type_name != "CategoryType":
            raise GraphQLError("Invalid ID type")

        try:
            category = Category.objects.get(pk=db_id)
        except Category.DoesNotExist:
            raise GraphQLError("Category not found")

        category.delete()
        return DeleteCategory(success=True)


# Tag mutations
class CreateTag(graphene.Mutation):
    tag = graphene.Field(TagType)

    class Arguments:
        name = graphene.String(required=True)

    def mutate(self, info, name):
        user = require_auth(info)
        require_role(user, ["journalist", "editor"])

        tag = Tag(name=name)
        tag.save()

        return CreateTag(tag=tag)


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

        type_name, db_id = from_global_id(category_id)
        if type_name != "CategoryType":
            raise GraphQLError("Invalid ID type")
        try:
            category = Category.objects.get(pk=db_id)
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
            tag_db_ids = []
            for tag in tag_ids:
                tag_type, tag_id = from_global_id(tag)
                if tag_type != "TagType":
                    raise GraphQLError("Invalid ID type")
                tag_db_ids.append(tag_id)

            tags = Tag.objects.filter(id__in=tag_db_ids)
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
        type_name, db_id = from_global_id(id)

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
            c_type, c_id = from_global_id(category_id)
            if c_type != "CategoryType":
                raise GraphQLError("Invalid ID type")
            try:
                category = Category.objects.get(pk=c_id)
            except Category.DoesNotExist:
                raise GraphQLError("Category not found")
            article.category = category

        if status is not None:
            article.status = status
            if status == "published":
                article.published_at = timezone.now()

        if is_featured is not None:
            article.is_featured = is_featured

        article.save()

        if tag_ids is not None:
            tag_db_ids = []
            for tag in tag_ids:
                tag_type, tag_id = from_global_id(tag)
                if tag_type != "TagType":
                    raise GraphQLError("Invalid ID type")
                tag_db_ids.append(tag_id)

            tags = Tag.objects.filter(id__in=tag_db_ids)
            article.tags.set(tags)

        return UpdateArticle(article=article)


class DeleteArticle(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        type_name, db_id = from_global_id(id)

        if type_name != "ArticleType":
            raise GraphQLError("Invalid ID type")

        user = require_auth(info)
        try:
            article = Article.objects.get(pk=db_id)
        except Article.DoesNotExist:
            raise GraphQLError("Article not found")
        if user != article.author and user.role != "editor":
            raise GraphQLError("Only the author or an editor can delete this article")

        article.delete()
        return DeleteArticle(success=True)


class LikeArticle(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        article_id = graphene.ID(required=True)

    def mutate(self, info, article_id):
        user = require_auth(info)

        type_name, db_id = from_global_id(article_id)
        if type_name != "ArticleType":
            raise GraphQLError("Invalid ID type")
        try:
            article = Article.objects.get(pk=db_id)
        except Article.DoesNotExist:
            raise GraphQLError("Article not found")

        like, created = Like.objects.get_or_create(article=article, user=user)

        if not created:
            # if like already exists, remove
            like.delete()
            return LikeArticle(success=False)

        return LikeArticle(success=True)


class BookmarkArticle(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        article_id = graphene.ID(required=True)

    def mutate(self, info, article_id):
        user = require_auth(info)

        type_name, db_id = from_global_id(article_id)
        if type_name != "ArticleType":
            raise GraphQLError("Invalid ID type")

        try:
            article = Article.objects.get(pk=db_id)
        except Article.DoesNotExist:
            raise GraphQLError("Article not found")

        bookmark, created = Bookmark.objects.get_or_create(article=article, user=user)

        if not created:
            # if bookmark already exists, remove
            bookmark.delete()
            return BookmarkArticle(success=False)

        return BookmarkArticle(success=True)


# Comment mutation
class AddComment(graphene.Mutation):
    comment = graphene.Field(CommentType)

    class Arguments:
        article_id = graphene.ID(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.ID()

    def mutate(self, info, article_id, content, parent_id=None):
        user = require_auth(info)

        type_name, db_id = from_global_id(article_id)
        if type_name != "ArticleType":
            raise GraphQLError("Invalid ID type")
        try:
            article = Article.objects.get(pk=db_id)
        except Article.DoesNotExist:
            raise GraphQLError("Article not found or not published")
        parent = None
        if parent_id:
            type_name, db_id = from_global_id(parent_id)
            if type_name != "CommentType":
                raise GraphQLError("Invalid ID type")
            try:
                parent = Comment.objects.get(pk=db_id)
            except Comment.DoesNotExist:
                raise GraphQLError("Comment not found")

        comment = Comment(article=article, user=user, content=content, parent=parent)

        comment.save()

        # from .subscriptions import comment_broadcast

        # comment_broadcast(comment)
        return AddComment(comment=comment)


class DeleteComment(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        user = require_auth(info)

        type_name, db_id = from_global_id(id)
        if type_name != "CommentType":
            raise GraphQLError("Invalid ID type")
        try:
            comment = Comment.objects.get(pk=db_id)
        except Comment.DoesNotExist:
            raise GraphQLError("Comment not found")

        if comment.user != user and user.role != "editor":
            raise GraphQLError("Only the author or an editor can delete this comment")
        comment.delete()
        return DeleteComment(success=True)


class Mutation(graphene.ObjectType):
    signup = Signup.Field()
    update_profile = UpdateProfile.Field()

    create_category = CreateCategory.Field()
    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()

    create_tag = CreateTag.Field()

    create_article = CreateArticle.Field()
    update_article = UpdateArticle.Field()
    delete_article = DeleteArticle.Field()
    like_article = LikeArticle.Field()
    bookmark_article = BookmarkArticle.Field()

    add_comment = AddComment.Field()
    delete_comment = DeleteComment.Field()

    # JWT helpers
    from graphql_jwt.shortcuts import get_token
    import graphql_jwt

    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
