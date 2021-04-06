import lkml

from lkml import (
    Lexer,
    Parser
)

from lkml.tree import (
    BlockNode,
    PairNode,
    SyntaxToken
)

from dataclasses import replace

from lkml.visitors import BasicTransformer

from funcs import (
    load_with_comments,
    generate_new_filename
)

import os

class AddLabel(BasicTransformer):
        def __init__(self, field_search, overwrite_confirmation=True, overwrite_override=False):
            # Create a properly formatted list from messy user input
            self.field_search = field_search.replace(' ', '').split(',')
            self.overwrite_confirmation = overwrite_confirmation
            self.overwrite_override = overwrite_override

        def visit_block(self, node: BlockNode) -> BlockNode:
            # We want to know if any of the search terms are present  
            if node.type.value not in ['view', 'explore'] and any(search_term.lower() in node.name.value for search_term in self.field_search):
                # Generate the new label to add
                new_label = PairNode(
                    SyntaxToken(value='group_label', prefix='', suffix=''),
                    SyntaxToken(value=label_name, prefix='', suffix='\n    ')
                )
                
                if not self.overwrite_override:
                    # We want to overwrite the group label, but should probably check to make sure it's okay first
                    if self.overwrite_confirmation:
                        overwrite = input(f'The field {node.name.value} already has a group_label parameter. Do you want to overwrite (Y/N):  ')
                        if overwrite.lower() not in ['n', 'no']:
                            pass
                        else:
                            try:
                                return self._visit_container(node)
                            except:
                                return node

                # If we got here, it means overwrite_confirmation == False or overwrite_override == True
                
                new_items = list(item for item in node.container.items if item.type.value != 'group_label')

                # Now we insert the group label at the front
                new_items.insert(0, new_label)

                # Replacing the original node's items with the new items
                new_container = replace(node.container, items=tuple(new_items))
                new_node = replace(node, container=new_container)

                # rebuild the tree with the new node and continue
                return new_node

            # We didn't match the search terms
            else:
                try:
                    return self._visit_container(node)
                # nodes that have ListNodes of type = 'filters' in them seem to be throwing FrozenInstanceError messages, 
                # but they still work and labels update if they match.
                except:
                    return node
                finally:
                    pass

print('''

######################################################################
Your project folder is the folder that contains your view folder, model
folder, and all your .lkml files
#######################################################################

''')

# Get the folder path from the user
lookml_base = os.path.normcase(input('Paste your project folder path and press Enter: '))
stop_trigger = ''

# Main loop, user can continue searching through with new terms/labels if they'd like
while stop_trigger.lower() not in ['n', 'no']:
    print('')
    field_search = input('What search terms are you looking for? Please separate multiple values with commas:  ')
    print('')
    label_name=f'"{input("What would you like the new label name to be?:  ")}"'
    print('')
    overwrite_override = input('''OVERWRITE CONFIRMATION

    |-----------------------------------------------------------------------------------------------|
    |  Choosing 'Y' will overwrite all group labels attached to field names that match your search  |
    |  Choosing 'N' will prompt you for each field name that has an existing group label            |
    |-----------------------------------------------------------------------------------------------|

    Would you like to turn off overwrite confirmation? (Y/N):  ''')
    if overwrite_override.lower() in ['n', 'no']:
        overwrite_override = False
    else:
        overwrite_override = True


    for folder in os.listdir(lookml_base):

        # First, let's only look at directories that don't start with periods (those are ones I added)
        if folder[0] != '.' and os.path.isdir(os.path.join(lookml_base, folder)) and folder != '__pycache__':

            for filename in os.listdir(os.path.join(lookml_base, folder)):

                # ignore any files beginning with a period, and any python or jupyter notebooks files (py or ipynb)
                if filename[0] != '.' and filename.split('.')[-1] not in ['py', 'ipynb', 'tmp', '__pycache__']:
                    
                    # Building the tree
                    lookml_path = os.path.join(lookml_base, folder, filename)
                    tree = load_with_comments(lookml_path)

                    # Add new labels
                    new_tree = tree.accept(AddLabel(field_search=field_search, overwrite_override=overwrite_override))

                    with open(lookml_path, 'w+') as new_file:
                        new_file.write(str(new_tree))

    # Done with this task, now we'll see if the user wants to keep going
    stop_trigger = input('''
    
    ##########################################################
    Finished generating new labels
    ##########################################################
    
    Would you like to add another group label with a different
    search query? (Y/N)

    Enter your response: ''')