import graphene # type: ignore
from .mutations import Mutation
from .queries import Query

schema = graphene.Schema(query=Query, mutation=Mutation)


