import io
import h5py
import numpy as np

def to_hdf5(ktype) -> io.BytesIO:

    data_bytes = io.BytesIO()
    with h5py.File(data_bytes, 'w') as hdf:
        
         # Store top-level attributes
        keys = ['id', 'name', 'created_at', 'updated_at']
        for key in keys:
            value = getattr(ktype, key)
            create_dataset(key, value, hdf)
        
        # Store the Webform
        webform = getattr(ktype, 'webform')
        webform_group = hdf.create_group('webform')
        if webform is not None:
            sections_group = webform_group.create_group('sections')
            section_keys = ['id', 'name', 'hidden']
            input_keys = ['measurement_unit', 'relation_mapping', 'relation_mapping_extra', 'range_options']
            for webform_key, webform_value in webform:
                if webform_key == 'kitem':
                    continue
                elif webform_key == 'sections':
                    for i, section in enumerate(webform_value):
                        section_group = sections_group.create_group(f'section_{i}')
                        for section_key in section_keys:
                            section_value = getattr(section, section_key)
                            create_dataset(section_key, section_value, section_group)
                        
                        inputs_group = section_group.create_group('inputs')

                        for j, input in enumerate(section.inputs):
                            input_group = inputs_group.create_group(f'input_{j}')
                            for input_key, input_value in input:
                                if input_key == 'kitem':
                                    continue
                                elif input_key == 'select_options':
                                    select_options_group = input_group.create_group('select_options')
                                    for k, select_option in enumerate(input_value):
                                        select_option_group = select_options_group.create_group(f'option_{k}')
                                        for option_key, option_value in select_option:                                            
                                            create_dataset(option_key, option_value, select_option_group)
                                elif input_key in input_keys and input_value is not None:
                                    group = input_group.create_group(input_key)
                                    for key_, value_ in input_value:
                                        if key_ == 'kitem':
                                            continue
                                        create_dataset(key_, value_, group)
                                else:
                                    create_dataset(input_key, input_value, input_group)
                    
                else:
                    create_dataset(webform_key, webform_value, webform_group)
    
    return data_bytes

def create_dataset(key, value, group):
    """Create dataset depending on the type of the data"""

    basic_types = (int, float, str, bool, list, tuple, dict, set)
    if isinstance(value, basic_types):
        group.create_dataset(key, data=value)
    else:
        group.create_dataset(key, data=str(value))