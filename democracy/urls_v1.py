from django.conf.urls import include, url
from rest_framework_nested import routers

from democracy.views import (
    CommentViewSet, ContactPersonViewSet, HearingViewSet, ImageViewSet, LabelViewSet, ProjectViewSet,
    RootSectionViewSet, SectionCommentViewSet, SectionViewSet, UserDataViewSet, FileViewSet, ServeFileView,
    AuthMethodViewSet
)

router = routers.DefaultRouter()
router.register(r'hearing', HearingViewSet, basename='hearing')
router.register(r'users', UserDataViewSet, basename='users')
router.register(r'comment', CommentViewSet, basename='comment')
router.register(r'image', ImageViewSet, basename='image')
router.register(r'section', RootSectionViewSet, basename='section')
router.register(r'label', LabelViewSet, basename='label')
router.register(r'contact_person', ContactPersonViewSet, basename='contact_person')
router.register(r'project', ProjectViewSet, basename='project')
router.register(r'file', FileViewSet, basename='file')
router.register(r'auth_method', AuthMethodViewSet, basename='auth_method')

hearing_child_router = routers.NestedSimpleRouter(router, r'hearing', lookup='hearing')
hearing_child_router.register(r'sections', SectionViewSet, basename='sections')

section_comments_router = routers.NestedSimpleRouter(hearing_child_router, r'sections', lookup='comment_parent')
section_comments_router.register(r'comments', SectionCommentViewSet, basename='comments')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(hearing_child_router.urls)),
    url(r'^', include(section_comments_router.urls)),
    url(r'^download/(?P<filetype>sectionfile|sectionimage)/(?P<pk>\d+)/$', ServeFileView.as_view(), name='serve_file'),
]
