from django.db import models
from treebeard.mp_tree import MP_Node


class ProjectCategory(MP_Node):
    ''' A hierarchical node for categorizing Projects to display them in a colapsing tree '''
    name = models.CharField(max_length=256) 
    node_order_by = ['name']

    class Meta:
        verbose_name_plural = "Project Categories"

    def __str__(self):
        ''' Returns the Name of the category for print() '''
        return self.name
    
    def display_for_user(self, user) -> bool:
        ''' Recursive function to show if ProjectCategory should show for a specific user based on showing or editing the Project. '''

        # Step through each project in this category and return True if they can view or edit it.
        for project in self.project_set.all():
            if user.has_perm('projects.change_project', project) or user.has_perm('projects.view_project', project):
                return True
        
        # Step through each child of this category and return True if they should be shown
        for child in self.get_children():
            if child.display_for_user(user): return True
        
        return False

    def tree_node(self, list: list=[], user=None, depth: int=0) -> dict:
        ''' Returns the tree node for the displayed list of nodes of Projects and Categories '''

        # If a user is supplied, check if they can see this project
        if user is None or self.display_for_user(user=user):
            children = []
            list.append({self.name: {'depth': depth+1, 'is_project': False, 'children': children}})

            for category in self.get_children():
                category.tree_node(user=user, depth=depth+1, list=children)
                
            for project in self.project_set.all():
                project.tree_node(user=user, depth=depth+1, list=children)
            
        return list


class Project(models.Model):
    ''' Projects corrispond with directories in PROJECT_PATH to load lineage data. '''
    name = models.CharField(max_length=256)
    category = models.ForeignKey(ProjectCategory, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        ''' Returns the Name of the project for print() '''
        return self.name

    def tree_node(self, list: list=[], user=None, depth: int=0) -> dict:
        ''' Returns the tree node for the displayed list of nodes of Projects and Categories '''

        # If a user is supplied, check if they can see this project
        if user is None or user.has_perm('projects.change_project', self) or user.has_perm('projects.view_project', self):
            list.append({self.name: {'depth': depth+1, 'is_project': True}})

        return list
    

class Tree(models.Model):
    """ An object that holds information about a specific tree in a project """
    name = models.CharField(max_length=256, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='trees')
    settings = models.JSONField(null=True, blank=True)

    def __str__(self):
        ''' Returns the name of the tree for print() '''
        return self.name