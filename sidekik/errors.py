'''blueprint for error handles'''

import flask

bp = flask.Blueprint("errors", __name__)

@bp.app_errorhandler(400)
def get_400(error):
    #db.session.rollback()
    return flask.render_template("errors/400.html"), 400

@bp.app_errorhandler(404)
def get_404(error):
    #db.session.rollback()
    return flask.render_template("errors/404.html"), 404

@bp.app_errorhandler(500)
def get_500(error):
    #db.session.rollback()
    return flask.render_template("errors/500.html"), 500


