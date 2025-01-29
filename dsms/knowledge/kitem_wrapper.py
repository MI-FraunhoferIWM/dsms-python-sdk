import io
import h5py
import numpy as np

def to_hdf5(kItem) -> io.BytesIO:
    """Export KItem to HDF5"""
    
    data_bytes = io.BytesIO()
    # with tempfile.NamedTemporaryFile(delete=False) as temp_file:
    with h5py.File(data_bytes, 'w') as hdf:
        
        # Store top-level attributes
        keys = ['name', 'id', 'ktype_id', 'in_backend', 'slug', 'avatar_exists', 'created_at', 'updated_at', 'rdf_exists', 'context_id', 'access_url']
        for key in keys:
            value = getattr(kItem, key)
            create_dataset(key, value, hdf)
        
        # Store the summary
        summary = getattr(kItem, 'summary')
        if summary is not None:
            if summary.text is not None:
                hdf.create_dataset('summary', data = summary.text)
        
        # Store dataframe
        dataframe = getattr(kItem, 'dataframe')
        if dataframe is not None:
            value = dataframe.to_df().to_json()
            hdf.create_dataset('dataframe', data = value)

        # Store the avatar in binary
        avatar = getattr(kItem, 'avatar')
        if avatar is not None:
            # Get the image
            image = avatar.download()

            # Create a BytesIO object and save the image to it
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')
            
            # Get the bytes value
            value = image_bytes.getvalue()
            img_arr = np.frombuffer(value, dtype=np.uint8)
            hdf.create_dataset('avatar', data=img_arr, dtype=img_arr.dtype)
        
        # Store the subgraph after serialization
        subgraph = getattr(kItem, 'subgraph')
        if subgraph is not None:
            value = subgraph.serialize()
            hdf.create_dataset('subgraph', data = value)  

        # Store annotations
        annotations_group = hdf.create_group('annotations')
        for i, annotation in enumerate(getattr(kItem, 'annotations')):
            annotation_group = annotations_group.create_group(f'annotation_{i}')
            for key, value in annotation:
                create_dataset(key, value, annotation_group)
        
        # Store attachments
        attachments_group = hdf.create_group('attachments')
        for i, attachment in enumerate(getattr(kItem,'attachments')):
            attachment_group = attachments_group.create_group(f'attachment_{i}')
            for key, value in attachment:
                if key == 'content':
                    value = attachment.download().encode()
                    binary_data = np.frombuffer(value, dtype='uint8')
                    attachment_group.create_dataset(key, data=binary_data, dtype=binary_data.dtype)
                else:
                    create_dataset(key, value, attachment_group)

        # Store linked_kitems
        linked_kitems_group = hdf.create_group('linked_kitems')
        for i, linked_kitem in enumerate(getattr(kItem,'linked_kitems')):
            linked_kitem_group = linked_kitems_group.create_group(f'linked_kitem_{i}')
            for key in ['id', 'name', 'slug', 'ktype_id']:
                value = getattr(linked_kitem, key)
                create_dataset(key, value, linked_kitem_group)

        # Store affiliations
        affiliations_group = hdf.create_group('affiliations')
        for i, affiliation in enumerate(getattr(kItem,'affiliations')):
            affiliation_group = affiliations_group.create_group(f'affiliation_{i}')
            for key, value in affiliation:
                create_dataset(key, value, affiliation_group)

        # Store authors
        authors_group = hdf.create_group('authors')
        for i, author in enumerate(getattr(kItem,'authors')):
            author_group = authors_group.create_group(f'author_{i}')
            for key, value in author:
                create_dataset(key, value, author_group)
        
        # Store contacts
        contacts_group = hdf.create_group('contacts')
        for i, contact in enumerate(getattr(kItem,'contacts')):
            contact_group = contacts_group.create_group(f'contact_{i}')
            for key, value in contact:
                create_dataset(key, value, contact_group)
        
        # Store external links
        external_links_group = hdf.create_group('external_links')
        for i, external_link in enumerate(getattr(kItem,'external_links')):
            external_link_group = external_links_group.create_group(f'external_link_{i}')
            for key, value in external_link:
                create_dataset(key, value, external_link_group)

        # Store kitem_apps
        kitem_apps_group = hdf.create_group('kitem_apps')
        for i, app in enumerate(getattr(kItem,'kitem_apps')):
            app_group = kitem_apps_group.create_group(f'app_{i}')
            for key, value in app:
                if key == 'additional_properties':
                    for prop_key, prop_value in value:
                        app_group.create_dataset(f'additional_properties/{prop_key}', data=prop_value)
                else:
                    create_dataset(key, value, app_group)

        # Store user groups
        user_groups_group = hdf.create_group('user_groups')
        for i, user_group in enumerate(getattr(kItem,'user_groups')):
            user_group_group = user_groups_group.create_group(f'user_group_{i}')
            for key, value in user_group:
                create_dataset(key, value, user_group_group)

        # Store custom_properties
        from dsms.knowledge.webform import KItemCustomPropertiesModel
        custom_properties_group = hdf.create_group('custom_properties')
        for item in kItem:
            if 'custom_properties' in item:
                break
        for custom_property in item:
            
            if isinstance(custom_property, KItemCustomPropertiesModel):
                sections_group = custom_properties_group.create_group('sections')
                for i, section in enumerate(custom_property):
                    section_group = sections_group.create_group(f'section_{i}')
                    section_group.create_dataset('id', data=section.id)
                    section_group.create_dataset('name', data=section.name)
                    entries_group = section_group.create_group('entries')

                    for j, entry in enumerate(section):
                        entry_group = entries_group.create_group(f'entry_{j}')

                        for key, value in entry:
                            if key == 'kitem':
                                continue
                            if key == 'measurement_unit':
                                measurement_unit_group = entry_group.create_group('measurement_unit')
                                for key_, value_ in value:
                                    if key_ == 'kitem':
                                        continue
                                    measurement_unit_group.create_dataset(key_, data=str(value_))
                            elif key == 'relation_mapping':
                                relation_mapping_group = entry_group.create_group('relation_mapping')
                                for key_, value_ in value:
                                    if key_ == 'kitem':
                                        continue 
                                    relation_mapping_group.create_dataset(key_, data=str(value_))
                            else:
                                create_dataset(key, value, entry_group)

    return data_bytes


def create_dataset(key, value, group):
    """Create dataset depending on the type of the data"""

    basic_types = (int, float, str, bool, list, tuple, dict, set)
    if isinstance(value, basic_types):
        group.create_dataset(key, data=value)
    else:
        group.create_dataset(key, data=str(value))
