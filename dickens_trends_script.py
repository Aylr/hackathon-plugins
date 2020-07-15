import great_expectations
from glob import glob

context = great_expectations.DataContext()

# TODO loading batches will move into DataContext eventually
batches_to_validate = []
for file in sorted(glob('annual/*.csv')):
    batch_kwargs = {'datasource': 'annual__dir', 'path': file}
    batch = context.get_batch(batch_kwargs, 'dickens_trends')
    results = context.run_validation_operator(
        'action_list_operator',
        assets_to_validate=[batch],
    )
    batch = context.get_batch(batch_kwargs, 'dickens_trends_2_the_second_one')
    results = context.run_validation_operator(
        'action_list_operator',
        assets_to_validate=[batch],
    )
