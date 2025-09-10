import graphene
from .queries import Query as NewsQuery
from .mutations import (
    Mutation as NewsMutation,
)


class Query(NewsQuery):
    pass


class Mutation(NewsMutation):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
