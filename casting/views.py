import random
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from casting.models import CastingUser, Choice
from casting.serializers import CastingUserSerializer, TopSerializer


class CastingUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint, которая позволяет просматривать, добавлять или редактировать
    участников голосования.
    """
    queryset = CastingUser.objects.all()
    serializer_class = CastingUserSerializer
    permission_classes = (IsAuthenticated,)

    @list_route(methods=['GET'])
    def top(self, request):
        """
        Топ N пользователей, позиции - индексы в списке
        """
        top_users = CastingUser.objects.order_by(
            '-rating')[:settings.USERS_ON_TOP_PAGE]
        resp = TopSerializer(top_users, many=True)
        return Response(resp.data)


class ChoiceUserViewSet(viewsets.ViewSet):
    '''
    API endpoint for creating unique user voting combinations
    and saving result of votes.
    '''
    queryset = Choice.objects.all()
    serializer_class = CastingUserSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        '''
        Create new choice and return uuids and photo url of users.
        '''
        users = random.sample(
            list(CastingUser.objects.order_by('counter')[:100]), 2)
        print(users)
        choice = Choice()
        choice.save()
        for user in users:
            choice.users.add(user)
        choice.save()
        resp = {
            'id': choice.id,
            'users': [
                {uuid: user.url} for uuid, user in choice.get_uuids().items()]
        }
        return Response(resp)

    def update(self, request, pk=None):
        if pk is not None:
            try:
                choice = Choice.objects.get(pk=pk)
            except Choice.DoesNotExist:
                return Response('Wrong choice id or choice already accepted',
                                status=status.HTTP_400_BAD_REQUEST)
            votedfor = request.data

            # update votes
            uuids = choice.get_uuids()
            if votedfor not in uuids.keys():
                return(Response('Current choice doesn\'t have that uuid',
                                status=status.HTTP_400_BAD_REQUEST))
            for uuid, user in choice.get_uuids().items():
                if uuid == votedfor:
                    user.rating += 1
                else:
                    user.rating -= 1
                user.counter += 1
                user.save()
            choice.delete()
        return(Response('You vote was accepted'))
