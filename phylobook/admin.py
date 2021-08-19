
from django.contrib import admin

from .models import Project

from guardian.admin import GuardedModelAdmin


class ProjectAdmin(GuardedModelAdmin):
    #prepopulated_fields = {"slug": ("title",)}
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

admin.site.register(Project, ProjectAdmin)