from flask import render_template, abort, flash, request,\
    current_app, jsonify, send_file
from werkzeug.utils import secure_filename

from . import main
from .. import cache
from ..models import save_access
import logging
from .forms import ProgramForm
import os

from ..qp import run_qikprop, OptionMap


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


@main.route('/', methods=['GET', 'POST'])
def index():
    form = ProgramForm()

    def debug(file, filename, kwargs):
        with open(filename, 'w') as f:
            f.write("")
        return filename

    # if form data is valid, go to success
    if form.validate_on_submit():
        file = form.input_file.data
        filename = secure_filename(file.filename)
        # file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        flash(f'Thank you for submitting {filename}, Data was uploaded, now processing...')
        # Extract options
        options = {option: getattr(form, option).data for option in OptionMap.known_methods() if option in form}

        # Run the code
        try:
            output_file = run_qikprop(file, filename, options)
            # output_file = debug(file, filename, {})
            return send_file(output_file, attachment_filename='qp_output.tar.gz', as_attachment=True)
        except Exception as e:
            flash(e)

    # return the empty form
    return render_template('covid/upload_data_form.html', form=form)


# Experimental, not working API sections
# @main.route('/api/', methods=['GET', 'POST'])
# def api_call():
#     # if not request.json:
#     #     abort(400)
#     print(request.args)
#     data = request.get_data()
#     incoming = request.files['data']
#     print(len(data))
#     print(incoming)
#     incoming.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'toy.csv'))
#     # with open(os.path.join(current_app.config['UPLOAD_FOLDER'], 'toy.csv'), 'wb') as f:
#     #     f.write(incoming)
#     return jsonify(request.json), 202


# Old ML datasets, probably remove
# @main.route('/ml_datasets/')
# def ml_datasets():
#
#     logger.info("ML Home page access.")
#     save_access(page='ml_datasets', access_type='homepage')
#
#     return render_template('ml_datasets.html')


# @main.route('/log_access/<access_type>/')
# def log_download(access_type):
#
#     logger.info('log_access: '.format(request.args))
#     ds_name = request.args.get('dataset_name', None)
#     ds_type = request.args.get('download_type', None)
#
#     save_access(page='ml_datasets', access_type=access_type,
#                 dataset_name=ds_name, download_type=ds_type)
#
#     return {'success': True}
