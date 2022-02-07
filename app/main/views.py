from flask import render_template, abort, flash, request,\
    current_app, send_from_directory
from werkzeug.utils import secure_filename

from . import main
from .hashing import generate_checksum_file
from .tasks import serve_file, run_qikprop_worker, inbound_staging, clear_output
from ..constants import QP_OUTPUT_TAR_NAME
from ..models import save_access
import logging
from .forms import ProgramForm
from pathlib import Path
import traceback

from ..qp import OptionMap


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


@main.route('/qpout/<checksum>')
def get_qp_output(checksum):
    possible_tarball = serve_file(checksum)
    if isinstance(possible_tarball, Path):
        fname = possible_tarball.name
        if QP_OUTPUT_TAR_NAME in possible_tarball.name:
            fname = QP_OUTPUT_TAR_NAME
        return send_from_directory(str(possible_tarball.parent),
                                   str(possible_tarball.name),
                                   filename=fname,
                                   as_attachment=True)
    elif isinstance(possible_tarball, str):
        return (f"Tasks for computations at ID {checksum} have not run or are not completed yet. "
                f"Please try again shortly")
    return f"Files for ID {checksum} are not ready yet. Please try again shortly."


@main.route('/clear/<checksum>')
def clear_qp_output(checksum):
    cleared = clear_output(checksum)
    if cleared:
        return f"Directory at hash {checksum} has been cleared"
    return f"No such output from {checksum} found. Nothing done"


@main.route('/', methods=['GET', 'POST'])
def index():
    form = ProgramForm()

    def debug(file, filename, kwargs):
        with open(filename, 'w') as f:
            f.write("")
        return filename

    # if form data is valid, go to success
    save_access(page="homepage", access_type='landing')
    if form.validate_on_submit():
        file = form.input_file.data
        checksum = generate_checksum_file(file)  # Function resets seek
        filename = secure_filename(file.filename)
        flash(f'Thank you for submitting {filename}, Data was uploaded, now processing under hash: {checksum}')
        # Extract options
        options = {option: getattr(form, option).data for option in OptionMap.known_methods() if option in form}
        save_access(page="homepage", access_type="run")
        # Run the code
        try:
            staged_file = inbound_staging(file, filename, checksum)
            print(f"File at invocation is {staged_file}")
            run_qikprop_worker.delay(str(staged_file), options, checksum)
            return render_template('covid/upload_data_form.html', form=form, hash=checksum)
        except Exception as e:
            save_access(page="homepage", access_type="run", error=str(e))
            flash(traceback.format_exc())

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
