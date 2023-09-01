import logging
log = logging.getLogger('app')

import os

from django.core.exceptions import ValidationError

from guardian.models import UserObjectPermission
from guardian.models import GroupObjectPermission

from phylobook.projects.models import Project


def merge_projects(*, project1: Project, project2: Project, new_project_name: str) -> bool:
    """ Merge two projects into one """

    # Check that the new project name is valid
    if Project.objects.filter(name=new_project_name).exists():
        raise Exception(f"Project with name {new_project_name} already exists")

    if " " in new_project_name:
            raise ValueError("Project name cannot contain spaces.")

    # Check that the projects are in a state to be merged
    if project1 == project2:
        raise ValueError("Cannot merge a project with itself")

    trees1 = project1.trees.all()
    trees2 = project2.trees.all()

    if set(trees1).intersection(set(trees2)):
        raise ValueError(f"Projects {project1.name} and {project2.name} have trees in common")

    if not os.path.exists(project1.files_path):
        raise ValueError(f"Project directory {project1.files_path} does not exist")
    
    if not os.path.exists(project2.files_path):
        raise ValueError(f"Project directory {project2.files_path} does not exist")
    files1: list = project1.files()
    files2: list = project2.files()

    if not files1:
        raise ValueError(f"Project directory {project1.files_path} is empty")
    
    if not files2:
        raise ValueError(f"Project directory {project2.files_path} is empty")
    
    if common_files := set(files1).intersection(set(files2)):
        print(common_files)
        raise Exception(f"Project directories {project1.files_path} and {project2.files_path} have {len(common_files)} files in common")
    
    # Harmonise permissions
    permissions1 = UserObjectPermission.objects.filter(object_pk=project1.pk, content_type_id=project1.content_type_id).values("user_id", "permission_id")
    permissions2 = UserObjectPermission.objects.filter(object_pk=project2.pk, content_type_id=project2.content_type_id).values("user_id", "permission_id")
    user_permissions = permissions1.union(permissions2)

    permissions1 = GroupObjectPermission.objects.filter(object_pk=project1.pk, content_type_id=project1.content_type_id).values("group_id", "permission_id")
    permissions2 = GroupObjectPermission.objects.filter(object_pk=project2.pk, content_type_id=project2.content_type_id).values("group_id", "permission_id")
    group_permissions = permissions1.union(permissions2)

    new_project = Project.objects.create(name=new_project_name, description=f"Merged project {project1.name} and {project2.name}")

    for permission in user_permissions:
        UserObjectPermission.objects.create(user_id=permission["user_id"], permission_id=permission["permission_id"], content_object=new_project)

    for permission in group_permissions:
        GroupObjectPermission.objects.create(group_id=permission["group_id"], permission_id=permission["permission_id"], content_object=new_project)

    for tree in trees1:
        tree.project=new_project
        tree.id=None
        tree.save()

    for tree in trees2:
        tree.project=new_project
        tree.id=None
        tree.save()

    project1.copy_files(name=new_project.name, overwrite=True)
    project2.copy_files(name=new_project.name, overwrite=True)

    return True
    