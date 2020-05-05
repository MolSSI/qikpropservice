from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response, send_from_directory
from werkzeug.utils import secure_filename

from . import main
from .. import cache
import qcportal as plt
from ..models import save_access
import logging
from .forms import UploadForm
import os


logger = logging.getLogger(__name__)

#  Logging to console in heroku
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)



@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/')
def index():
    apps = [
        {'name': 'Machine Learning Datasets', 'link': '/ml_datasets/'},
        {'name': 'MolSSI COIVD Form template', 'link': '/covid_form/'},

    ]
    return render_template('index.html', apps=apps)


@main.route('/covid_form/', methods=['GET', 'POST'])
def app_in_iframe():
    form = UploadForm()

    # if form data is valid, go to success
    if form.validate_on_submit():
        file = form.data_file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        flash(f'Thank you {form.name.data}, Data was uploaded successfully')

        # return redirect('/thank_you')

    # return the empty form
    return render_template('covid/upload_data_form.html', form=form)


@main.route('/ml_datasets/')
def ml_datasets():

    logger.info("ML Home page access.")
    save_access(page='ml_datasets', access_type='homepage')

    return render_template('ml_datasets.html')

@main.route('/log_access/<access_type>/')
def log_download(access_type):

    logger.info('log_access: '.format(request.args))
    ds_name = request.args.get('dataset_name', None)
    ds_type = request.args.get('download_type', None)

    save_access(page='ml_datasets', access_type=access_type,
                dataset_name=ds_name, download_type=ds_type)

    return {'success': True}

@cache.cached()  # timeout in config
def _get_qcarchive_collections():
    """Get Machine Learning datasets from QCArchive server"""

    # connection client to MolSSI server
    client = plt.FractalClient()

    collection_types = ['dataset', 'reactiondataset']

    payload = {
        "meta": {
            "exclude": ["records", "contributed_values"],
        },
        "data": {"collection": None}
    }

    results = []
    for type in collection_types:
        # must have the type to use exclude functionality
        payload['data']['collection'] = type
        # HTTP request to load the data
        res = client._automodel_request("collection", "get", payload, full_return=False)
        results.extend(res)

    logger.debug('Total collections fetched: ', len(results))

    data = []
    for r in results:
        if "machine learning" in r["tags"]:
            r["tags"].remove("machine learning")
        else:   # skip non ML datasets
            continue

        if r['metadata']:  # add metadata attributes
            r.update(r.pop("metadata"))


        r['data_points'] = f'{r["data_points"]:,}'

        if r['view_metadata']:  # add metadata attributes
            r.update(r.pop("view_metadata"))
            # sizes from bytes to MB
            r['plaintext_size'] = int(r['plaintext_size']) // 1024**2
            r['plaintext_size'] = f'{r["plaintext_size"]:,}'

            r['hdf5_size'] = int(r['hdf5_size']) // 1024**2
            r['hdf5_size'] = f'{r["hdf5_size"]:,}'

        data.append(r)

    return data


@main.route('/ml_datasets_list/')
def ml_datasets_list():

    data = _get_qcarchive_collections()

    return {'data': data}