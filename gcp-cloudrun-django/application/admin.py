from django.contrib import admin


class ApplicationAdminSite(admin.AdminSite):
    site_title = 'Cloud Run Backend'
    site_header = site_title
    index_title = 'Cloud Run Backend Configuration'
