from django.conf.urls import patterns, url
from gmail import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^email$', views.EmailList.as_view(), name='email_list'),
    url(r'^email/resource/(?P<eid>\w+)$', views.Resource.as_view()),
    url(r'^email/resource/(?P<eid>\w+)/(?P<idx>\d+)$', views.Resource.as_view(), name='resource'),
    url(r'^email/search$', views.Search.as_view(), name='email_search'),
    url(r'^email/(?P<eid>\w{24})$', views.EmailDetail.as_view(), name='email_detail'),
    # Examples:
    # url(r'^$', 'prism.views.home', name='home'),
    # url(r'^prism/', include('prism.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
