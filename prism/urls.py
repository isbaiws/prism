from django.conf.urls import patterns, url
from gmail import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # url(r'^$', views.Index.as_view(), name='index'),
    url(r'^$', views.EmailList.as_view(), name='index'),

    url(r'^login$', views.Login.as_view(), name='login'),
    url(r'^logout$', views.Logout.as_view(), name='logout'),

    url(r'^user/$', views.UserList.as_view(), name='user_list'),
    url(r'^user/edit/$', views.UserEdit.as_view(), name='user_edit', kwargs={'uid': None}),
    url(r'^user/edit/(?P<uid>\w{24})$', views.UserEdit.as_view(), name='user_edit'),
    url(r'^user/password/edit/$', views.PasswordEdit.as_view(), name='user_password_reset', kwargs={'uid': None}),
    url(r'^user/password/edit/(?P<uid>\w{24})$', views.PasswordEdit.as_view(), name='user_password_reset'),
    url(r'^user/add/$', views.UserAdd.as_view(), name='user_add'),
    url(r'^user/delete/$', views.UserDelete.as_view(), name='user_delete', kwargs={'uid': None}),
    url(r'^user/delete/(?P<uid>\w{24})$', views.UserDelete.as_view(), name='user_delete'),

    url(r'^group/$', views.GroupList.as_view(), name='group_list'),
    url(r'^group/add/$', views.GroupAdd.as_view(), name='group_add'),
    url(r'^group/edit/(?P<gid>\w{24})$', views.GroupEdit.as_view(), name='group_edit'),
    url(r'^group/delete/(?P<gid>\w{24})$', views.GroupDelete.as_view(), name='group_delete'),

    # url(r'^email$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/folder/$', views.EmailList.as_view(), name='email_list', kwargs={'folder': None}),
    url(r'^email/folder/(?P<folder>.+)/$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/resource/(?P<rid>\w{24})$', views.Resource.as_view(), name='resource'),
    url(r'^email/search/$', views.Search.as_view(), name='email_search'),
    url(r'^email/(?P<folder>.+)/timeline/$', views.TimeLine.as_view(), name='email_timeline'),
    url(r'^email/timeline/$', views.TimeLine.as_view(), name='email_timeline', kwargs={'folder': None}),
    url(r'^email/(?P<folder>.+)/timeline\.json$', views.TimeLineJson.as_view(), name='email_timeline_json'),
    url(r'^email/timeline\.json$', views.TimeLineJson.as_view(), name='email_timeline_json', kwargs={'folder': None}),
    url(r'^email/(?P<folder>.+)/relation/$', views.Relation.as_view(), name='email_relation'),
    url(r'^email/relation/$', views.Relation.as_view(), name='email_relation', kwargs={'folder': None}),
    url(r'^email/(?P<folder>.+)/relation\.json$', views.RelationJson.as_view(), name='email_relation_json'),
    url(r'^email/relation\.json$', views.RelationJson.as_view(), name='email_relation_json', kwargs={'folder': None}),
    # url(r'^email/timeline\.json$', views.TimeLine.as_view(), {'is_ajax': True}, name='email_timeline_ajax'),
    url(r'^email/(?P<folder>.+)/statistics/$', views.Statistics.as_view(), name='email_statistics'),
    url(r'^email/statistics/$', views.Statistics.as_view(), name='email_statistics', kwargs={'folder': None}),
    url(r'^email/(?P<folder>.+)/statistics\.json$', views.StatisticsJson.as_view(), name='email_statistics_json'),
    url(r'^email/statistics\.json$', views.StatisticsJson.as_view(), name='email_statistics_json', kwargs={'folder': None}),
    url(r'^email/(?P<eid>\w{24})$', views.EmailDetail.as_view(), name='email_detail'),
    url(r'^email/(?P<eid>\w{24})/delete$', views.Delete.as_view(), name='email_delete'),
    url(r'^email/delete$', views.Delete.as_view(), name='email_delete'),

    url(r'^api/upload$', views.ApiUpload.as_view(), name='api_upload'),
    url(r'^api/init$', views.ApiInit.as_view(), name='api_init'),
    url(r'^api/login$', views.ApiLogin.as_view(), name='api_login'),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^not-implemented$', views.not_implemented, name='not_implemented'),
    # url(r'^debug$', views.debug, name='debug'),
)
