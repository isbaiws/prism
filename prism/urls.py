from django.conf.urls import patterns, url
from gmail import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.Index.as_view(), name='index'),

    url(r'^login$', views.Login.as_view(), name='login'),
    url(r'^logout$', views.Logout.as_view(), name='logout'),

    url(r'^user$', views.UserDetail.as_view(), name='user_detail'),
    url(r'^user/add$', views.AddUser.as_view(), name='user_add'),

    # url(r'^email$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/path$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/path/(?P<path>.+)$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/resource/(?P<rid>\w{24})$', views.Resource.as_view(), name='resource'),
    url(r'^email/search$', views.Search.as_view(), name='email_search'),
    url(r'^email/timeline$', views.TimeLine.as_view(), name='email_timeline'),
    # url(r'^email/timeline\.json$', views.TimeLine.as_view(), {'is_ajax': True}, name='email_timeline_ajax'),
    url(r'^email/(?P<eid>\w{24})$', views.EmailDetail.as_view(), name='email_detail'),
    url(r'^email/(?P<eid>\w{24})/delete$', views.Delete.as_view(), name='delete_email'),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^not-implemented$', views.not_implemented, name='not_implemented'),
)
