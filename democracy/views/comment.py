# -*- coding: utf-8 -*-
import django_filters
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_text
from rest_framework import permissions, response, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.settings import api_settings
from reversion import revisions

from democracy.models.comment import BaseComment
from democracy.models.section import Section
from democracy.models.hearing import Hearing
from democracy.views.base import AdminsSeeUnpublishedMixin, CreatedBySerializer
from democracy.views.utils import GeoJSONField, AbstractSerializerMixin
from democracy.renderers import GeoJSONRenderer

COMMENT_FIELDS = ['id', 'content', 'author_name', 'n_votes', 'created_at', 'is_registered', 'can_edit',
                  'geojson', 'map_comment_text', 'images', 'label', 'organization', 'flagged']


class BaseCommentSerializer(AbstractSerializerMixin, CreatedBySerializer, serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    flagged = serializers.SerializerMethodField()
    geojson = GeoJSONField()

    def to_representation(self, instance):
        r = super().to_representation(instance)
        request = self.context.get('request', None)
        if request:
            if request.GET.get('include', None) == 'plugin_data':
                r['plugin_data'] = instance.plugin_data
        return r

    def get_is_registered(self, obj):
        return obj.created_by_id is not None

    def get_can_edit(self, obj):
        request = self.context.get('request', None)
        '''
        Users that have is_staff and that are the creators of the hearing can edit/delete comments
        as long as the hearing is commentable.
        '''
        # If user.is_staff then we check if user is also the creator of the hearing
        if request.user.is_staff and Section.objects.get(id=obj.section_id) is not None:
            specific_section = Section.objects.get(id=obj.section_id)
            specific_hearing = Hearing.objects.get(id=specific_section.hearing_id)
            if request.user.id == specific_hearing.created_by_id:
                try:
                    obj.parent.check_commenting(request)
                except ValidationError:
                    return False
                return True

        if request:
            return obj.can_edit(request)
        return False

    def get_organization(self, obj):
        if obj.organization:
            return str(obj.organization)
        return None

    def get_flagged(self, obj):
        return bool(obj.flagged_at)

    class Meta:
        model = BaseComment
        fields = COMMENT_FIELDS


class BaseCommentFilterSet(django_filters.rest_framework.FilterSet):
    authorization_code = django_filters.CharFilter()

    class Meta:
        model = BaseComment
        fields = ['authorization_code', ]


class BaseCommentViewSet(AdminsSeeUnpublishedMixin, viewsets.ModelViewSet):
    """
    Base viewset for comments.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = None
    edit_serializer_class = None
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = BaseCommentFilterSet
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [GeoJSONRenderer, ]

    def get_serializer(self, *args, **kwargs):
        serializer_class = kwargs.pop("serializer_class", None) or self.get_serializer_class()
        context = kwargs['context'] = self.get_serializer_context()
        if serializer_class is self.edit_serializer_class and "data" in kwargs:  # Creating things with data?
            # So inject a reference to the parent object
            data = kwargs["data"].copy()
            data[serializer_class.Meta.model.parent_field] = context["comment_parent"]
            kwargs["data"] = data
        return serializer_class(*args, **kwargs)

    def get_comment_parent_id(self):
        # this is introduced to kwargs directly from URL!
        return self.kwargs.get("comment_parent_pk", None)

    def get_comment_parent(self):
        """
        :rtype: Commentable
        """
        return self.get_queryset().model.parent_model.objects.get(pk=self.get_comment_parent_id())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["comment_parent"] = self.get_comment_parent_id()
        return context

    def get_queryset(self):
        """
        This method is used  when fetching reply comments only.
        Returns all sub-comments, including deleted ones
        """

        queryset = self.model.objects.everything()
        queryset = queryset.filter(**{queryset.model.parent_field: self.get_comment_parent_id()})

        user = self._get_user_from_request_or_context()
        if user.is_authenticated and user.is_superuser:
            return queryset
        else:
            return queryset.exclude(published=False)

    def create_related(self, request, instance=None, *args, **kwargs):
        pass

    def update_related(self, request, instance=None, *args, **kwargs):
        pass

    def _check_may_comment(self, request):
        parent = self.get_comment_parent()
        try:
            # The `assert` checks that the function adheres to the protocol defined in `Commenting`.
            assert parent.check_commenting(request) is None
        except ValidationError as verr:
            return response.Response(
                {'status': force_text(verr), 'code': verr.code},
                status=status.HTTP_403_FORBIDDEN
            )

    def _check_may_vote(self, request):
        parent = self.get_comment_parent()
        try:
            # The `assert` checks that the function adheres to the protocol defined in `Commenting`.
            assert parent.check_voting(request) is None
        except ValidationError as verr:
            return response.Response(
                {'status': force_text(verr), 'code': verr.code},
                status=status.HTTP_403_FORBIDDEN
            )
    
    def _check_hearing_creator(self, request):
        '''
        Returns boolean based on if request.user has is_staff rights, is the creator of the hearing
        and if the hearing is commentable.
        '''
        obj = self.get_object()
        if request.user.is_staff and Section.objects.get(id=obj.section_id) is not None:
            specific_section = Section.objects.get(id=obj.section_id)
            specific_hearing = Hearing.objects.get(id=specific_section.hearing_id)
            if request.user.id == specific_hearing.created_by_id:
                try:
                    obj.parent.check_commenting(request)
                except ValidationError:
                    return False
                return True
        return False


    def create(self, request, *args, **kwargs):
        resp = self._check_may_comment(request)
        if resp:
            return resp

        # Use one serializer for creation,
        serializer = self.get_serializer(serializer_class=self.edit_serializer_class, data=request.data)
        serializer.is_valid(raise_exception=True)
        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user
        comment = serializer.save(**kwargs)
        # and another for the response
        serializer = self.get_serializer(instance=comment)
        self.create_related(request, instance=comment, *args, **kwargs)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        resp = self._check_may_comment(request)
        if resp:
            return resp

        instance = self.get_object()
        '''
        Comment editing is only possible if the comment is created by user OR
        if the user has is_staff rights AND is the creator of the hearing that this comment is in.
        '''
        if not self._check_hearing_creator(request) and self.request.user != instance.created_by:
            return response.Response(
                {'status': 'You do not have sufficient rights to edit a comment not owned by you.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if request.user.is_authenticated and 'author_name' in request.data:
            if request.data['author_name'] != instance.author_name:
                return response.Response(
                    {'status': 'Authenticated users cannot set author name.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Use one serializer for update,
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance=instance,
                                         serializer_class=self.edit_serializer_class,
                                         data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.refresh_from_db()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # and another for the response
        serializer = self.get_serializer(instance=instance)
        self.update_related(request, instance=instance, *args, **kwargs)
        return response.Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        resp = self._check_may_comment(request)
        if resp:
            return resp

        instance = self.get_object()
        '''
        Comment deletion is only possible if the comment is created by user OR
        if the user has is_staff rights AND is the creator of the hearing that this comment is in.
        '''
        if not self._check_hearing_creator(request) and self.request.user != instance.created_by:
            return response.Response(
                {'status': 'You do not have sufficient rights to delete a comment not owned by you.'},
                status=status.HTTP_403_FORBIDDEN
            )

        instance.soft_delete(user=request.user)
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        with transaction.atomic(), revisions.create_revision():
            super().perform_update(serializer)

    @action(detail=True, methods=['post'])
    def vote(self, request, **kwargs):
        resp = self._check_may_vote(request)
        if resp:
            return resp
        comment = self.get_object()

        if not request.user.is_authenticated:
            # If the check went through, anonymous voting is allowed
            comment.n_unregistered_votes += 1
            comment.recache_n_votes()
            return response.Response({'status': 'Vote has been counted'}, status=status.HTTP_200_OK)
        # Check if user voted already. If yes, return 304.
        if comment.__class__.objects.filter(id=comment.id, voters=request.user).exists():
            return response.Response({'status': 'Already voted'}, status=status.HTTP_304_NOT_MODIFIED)
        # add voter
        comment.voters.add(request.user)
        # update number of votes
        comment.recache_n_votes()
        # return success
        return response.Response({'status': 'Vote has been added'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def flag(self, request, **kwargs):
        instance = self.get_object()
        user = request.user
        # Only hearing organization admins can flag comments
        if instance.section.hearing.organization not in user.admin_organizations.all():
            return response.Response(
                {'status': "You don't have authorization to flag this comment"}, status=status.HTTP_403_FORBIDDEN
            )
        if instance.flagged_at:
            return response.Response({'status': 'Already flagged'}, status=status.HTTP_304_NOT_MODIFIED)

        instance.flagged_at = timezone.now()
        instance.flagged_by = request.user
        instance.save()
        return response.Response({'status': 'comment flagged'})

    @action(detail=True, methods=['post'])
    def unvote(self, request, **kwargs):
        # Return 403 if user is not authenticated
        if not request.user.is_authenticated:
            return response.Response({'status': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        comment = self.get_object()

        # Check if user voted already. If yes, return 400.
        if comment.__class__.objects.filter(id=comment.id, voters=request.user).exists():
            # remove voter
            comment.voters.remove(request.user)
            # update number of votes
            comment.recache_n_votes()
            # return success
            return response.Response({'status': 'Removed vote'}, status=status.HTTP_204_NO_CONTENT)

        return response.Response({'status': 'You have not voted for this comment'}, status=status.HTTP_304_NOT_MODIFIED)



    @action(detail=True, methods=['delete'])
    def delete(self, request, **kwargs):
        instance = self.get_object()
        user = request.user
        if instance.section.hearing.organization not in user.admin_organizations.all() and not user.is_staff:
            return response.Response(
                {'status': "You don't have authorization to delete this comment"}, status=status.HTTP_403_FORBIDDEN
            )
        
        instance.soft_delete(user=request.user)
        return response.Response({'status': 'Comment deleted'})
    

    @action(detail=True, methods=['post'])
    def unflag(self, request, **kwargs):
        instance = self.get_object()
        user = request.user
        if instance.section.hearing.organization not in user.admin_organizations.all() and not user.is_staff:
            return response.Response(
                {'status': "You don't have authorization to unflag this comment"}, status=status.HTTP_403_FORBIDDEN
            )
        if not instance.flagged_at:
            return response.Response({'status': 'Not flagged'}, status=status.HTTP_304_NOT_MODIFIED)

        instance.flagged_at = None
        instance.flagged_by = None
        instance.save()
        return response.Response({'status': 'Comment unflagged'})