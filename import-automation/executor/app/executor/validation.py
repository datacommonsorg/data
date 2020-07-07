from app import utils


TASK_INFO_REQUIRED_FIELDS = ['REPO_NAME', 'BRANCH_NAME', 'COMMIT_SHA', 'PR_NUMBER']
MANIFEST_REQUIRED_FIELDS = []
IMPROT_SPEC_REQUIRED_FIELDS = []


def import_targets_valid(import_targets, manifest_dirs):
    import_all = 'all' in import_targets
    if not import_targets:
        return False, 'No import target specified in commit message'
    relative_names = utils.get_relative_import_names(import_targets)
    if not import_all and len(manifest_dirs) > 1 and relative_names:
        err_template = 'Commit touched multiple directories {} but {} are relative import names'
        err = err_template.format(
            utils.list_to_str(manifest_dirs), utils.list_to_str(relative_names))
        return False, err
    return True, ''


def import_spec_valid(import_spec):
    pass


def manifest_valid(manifest):
    pass


def task_info_valid(task_info):
    missing_keys = get_missing_keys(TASK_INFO_REQUIRED_FIELDS, task_info)
    if missing_keys:
        return False, 'Missing {} in task info'.format(', '.join(missing_keys))

    return True, ''


def get_missing_keys(keys, a_dict):
    return list(key for key in keys if key not in a_dict)
