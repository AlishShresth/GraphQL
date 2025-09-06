import functools
from graphql import GraphQLError
from django.contrib.auth.models import AnonymousUser


def journalist_required(func):
    @functools.wraps(func)
    def wrapper(root, info, **kwargs):
        user = info.context.user

        if isinstance(user, AnonymousUser):
            raise GraphQLError("You must be logged in to perform this action")

        if not user.is_journalist and not user.is_editor:
            raise GraphQLError(
                "You must be a journalist or editor to perform this action"
            )

        return func(root, info, **kwargs)

    return wrapper


def editor_required(func):
    @functools.wrap(func)
    def wrapper(root, info, **kwargs):
        user = info.context.user

        if isinstance(user, AnonymousUser):
            raise GraphQLError("You must be logged in to perform this action")

        if not user.is_editor:
            raise GraphQLError("You must be an editor to perform this action")

        return func(root, info, **kwargs)

    return wrapper


def author_required(func):
    @functools.wrap(func)
    def wrapper(root, info, **kwargs):
        user = info.context.user

        if isinstance(user, AnonymousUser):
            raise GraphQLError("You must be logged in to perform this action")

        # check if the user is the author of the article or an editor
        article_id = kwargs.get("id") or kwargs.get("articleId")
        if article_id:
            from news.models import Article

            try:
                article = Article.objects.get(pk=article_id)
                if user != article.author and not user.is_editor:
                    raise GraphQLError(
                        "You must be the author of this article or an editor to perform this action"
                    )
            except Article.DoesNotExist:
                raise GraphQLError("Article not found")

        return func(root, info, **kwargs)

    return wrapper


def comment_author_required(func):
    @functools.wraps(func)
    def wrapper(root, info, **kwargs):
        user = info.context.user

        if isinstance(user, AnonymousUser):
            raise GraphQLError("You must be logged in to perform this action")

        # Check if the user is the author of the comment or an editor
        comment_id = kwargs.get("id")
        if comment_id:
            from news.models import Comment

            try:
                comment = Comment.objects.get(pk=comment_id)
                if user != comment.user and not user.is_editor:
                    raise GraphQLError(
                        "You must be the author of this comment or an editor to perform this action"
                    )

            except Comment.DoesNotExist:
                raise GraphQLError("Comment not found")

            return func(root, info, **kwargs)

        return wrapper
