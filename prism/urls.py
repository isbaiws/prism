from django.conf.urls import patterns, url
from gmail import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.Index.as_view(), name='index'),

    url(r'^login$', views.Login.as_view(), name='login'),
    url(r'^logout$', views.Logout.as_view(), name='logout'),

    url(r'^user$', views.UserList.as_view(), name='user_list'),
    url(r'^user/edit$', views.UserEdit.as_view(), name='user_edit'),
    url(r'^user/password/edit$', views.PasswordEdit.as_view(), name='user_password_reset'),
    url(r'^user/add$', views.AddUser.as_view(), name='user_add'),

    url(r'^group$', views.GroupList.as_view(), name='group_list'),
    url(r'^group/add$', views.GroupAdd.as_view(), name='group_add'),

    # url(r'^email$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/folder$', views.EmailList.as_view(), name='email_list', kwargs={'folder': None}),
    url(r'^email/folder/(?P<folder>.+)$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/resource/(?P<rid>\w{24})$', views.Resource.as_view(), name='resource'),
    url(r'^email/search$', views.Search.as_view(), name='email_search'),
    url(r'^email/(?P<folder>.+)/timeline$', views.TimeLine.as_view(), name='email_timeline'),
    url(r'^email/timeline$', views.TimeLine.as_view(), name='email_timeline', kwargs={'folder': None}),
    url(r'^email/(?P<folder>.+)/timeline\.json$', views.TimeLineJson.as_view(), name='email_timeline_json'),
    url(r'^email/timeline\.json$', views.TimeLineJson.as_view(), name='email_timeline_json', kwargs={'folder': None}),
    url(r'^email/(?P<folder>.+)/relation$', views.Relation.as_view(), name='email_relation'),
    url(r'^email/relation$', views.Relation.as_view(), name='email_relation', kwargs={'folder': None}),
    url(r'^email/(?P<folder>.+)/relation\.json$', views.RelationJson.as_view(), name='email_relation_json'),
    url(r'^email/relation\.json$', views.RelationJson.as_view(), name='email_relation_json', kwargs={'folder': None}),
    # url(r'^email/timeline\.json$', views.TimeLine.as_view(), {'is_ajax': True}, name='email_timeline_ajax'),
    url(r'^email/(?P<eid>\w{24})$', views.EmailDetail.as_view(), name='email_detail'),
    url(r'^email/(?P<eid>\w{24})/delete$', views.Delete.as_view(), name='delete_email'),

    url(r'^api/upload$', views.ApiUpload.as_view(), name='api_upload'),
    url(r'^api/init$', views.ApiInit.as_view(), name='api_init'),
    url(r'^api/login$', views.ApiLogin.as_view(), name='api_login'),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^not-implemented$', views.not_implemented, name='not_implemented'),
    url(r'^debug$', views.debug, name='debug'),
)
