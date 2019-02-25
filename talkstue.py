from app import create_app, cli, db
from app.core import models as core_models
from app.auth import models as auth_models

app = create_app()
cli.register(app)

def get_all_in_all(module):
    return {
        model_name: getattr(module, model_name, None)
        for model_name in module.__all__
    }

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        **get_all_in_all(core_models),
        **get_all_in_all(auth_models),
    }

if __name__ == '__main__':
    app.run()
