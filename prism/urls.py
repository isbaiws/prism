from django.conf.urls import patterns, include, url
from gmail import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^emails$', views.EmailList.as_view(), name='email_list'),
    url(r'^emails/(?P<eid>\w+)$', views.EmailDetail.as_view(), name='email_detail'),
    # Examples:
    # url(r'^$', 'prism.views.home', name='home'),
    # url(r'^prism/', include('prism.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
