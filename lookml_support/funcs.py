import lkml

from lkml import (
    Lexer,
    Parser
)

def load_with_comments(lookml_path):
    '''
    Parses LookML , but doesn't remove comments

    '''
    with open(lookml_path, 'r+') as orig_file:
        text = orig_file.read()
    lexer=Lexer(text)
    tokens = lexer.scan()
    parser = Parser(tokens)
    tree = parser.parse()
    return tree

def generate_new_filename(lookml_path, extension):
    lookml_filename_new = lookml_path.split('\\')[-1].split('.')
    lookml_filename_new[0] += extension
    return '.'.join(lookml_filename_new)


def find(lst, key, value):
    '''
    Finds a value in a list of dictionaries
    '''
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return f'Value "{value}" not found'
    

def generate_sets(lookml_path, view_name):
    '''
    Automatically generate sets for each dimension group in a view
    '''

    with open(lookml_path, 'r+') as file:
        result = lkml.load(file)

    view_list = result['views']

    # get the view number index from list of dictionaries
    view_num = find(view_list, 'name', view_name)
    
    # Are there any dimension groups in this view?
    try:
        dim_group_count = len(view_list[view_num]['dimension_groups'])

    except:
        return f'No dimension groups in {view_name} view'

    # Yay! There's at least one dimension group.
    # Now, are there any sets in this dimension group?
    try:
        current_set_list = view_list[view_num]['sets']

    # There weren't any sets, but that's okay. We'll create a new one.
    except:
        current_set_list[view_num]['sets'] = []

    # Creating some tracking info
    new_set_names = []

    # Iterate through dimension groups and generate sets based on the
    # timeframes in the dimension group
    for dim_group in view_list[view_num]['dimension_groups']:

        # extracting info from the dimension group and creating
        # variables to be used in set generation
        dim_group_type = dim_group['type']
        dim_group_name = dim_group['name']
        dim_group_timeframes = dim_group['timeframes']
        new_set_name = f'{dim_group_name}_{dim_group_type}_fields'

        # there are different naming formats for duration vs. time types, so we need to build different field name
        # lists for the different types
        if dim_group_type == 'time':
            field_names = [dim_group_name + '_' + timeframe for timeframe in dim_group_timeframes]
        elif dim_group_type == 'duration':
            field_names = [timeframe + '_' + dim_group_name for timeframe in dim_group_timeframes]

        view_list[view_num]['sets'].append(
            {'fields': field_names,
        'name': new_set_name}
        )

        new_set_names.append(new_set_name)

    print(f'Created the following {dim_group_count} new sets:')
    [print(set_name) for set_name in new_set_names]

    orig_lookml_filename = lookml_path.split('\\')[-1]

    new_lookml_filename = generate_new_filename(lookml_path, '_new')

    lookml_new_path = lookml_path.replace(orig_lookml_filename, new_lookml_filename)

    with open(f'{lookml_new_path}', 'w+') as new_file:
        lkml.dump(result, new_file)
    