from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns(
    '',
    url(r'^accounts/login/$',
        'accounts.views.login',
        {'template_name': 'accounts/login.html'}, name="user-login"),
    url(r'^accounts/logout/$',
        'django.contrib.auth.views.logout_then_login', name="user-logout")
)
