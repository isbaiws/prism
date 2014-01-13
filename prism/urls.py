from django.conf.urls import patterns, url
from django.contrib.auth.views import logout
from gmail import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.Index.as_view(), name='index'),

    url(r'^login$', views.Login.as_view(), name='login'),
    url(r'^logout$', views.Logout.as_view(), name='logout'),

    url(r'^user/add$', views.AddUser.as_view(), name='add_user'),
    url(r'^user$', views.UserDetail.as_view(), name='user_detail'),

    url(r'^email$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/resource/(?P<rid>\w{24})$', views.Resource.as_view(), name='resource'),
    url(r'^email/search$', views.Search.as_view(), name='email_search'),
    url(r'^email/(?P<eid>\w{24})$', views.EmailDetail.as_view(), name='email_detail'),
    url(r'^email/(?P<eid>\w{24})/delete$', views.Delete.as_view(), name='delete_email'),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
