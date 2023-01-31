from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from phylobook.projects.models import Project, ProjectCategory
from guardian.admin import GuardedModelAdmin


@admin.register(Project)
class ProjectAdmin(GuardedModelAdmin):
    list_display = ('name', 'category')
    list_editable = ('category',)
    search_fields = ('name',)
    ordering = ('category', 'name')


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(TreeAdmin):
    form = movenodeform_factory(ProjectCategory)