import logging
from absl import flags

FLAGS = flags.FLAGS

def handle_initialize_database(spanner, request_json):
    """Initializes the database by creating all required tables and proto bundles."""
    logging.info("Action: initialize_database")
    enable_embeddings = request_json.get('enableEmbeddings',
                                         FLAGS.enable_embeddings)
    spanner.initialize_database(enable_embeddings=enable_embeddings)
    return ('OK', 200)

def handle_seed_database(spanner):
    """Seeds the database with base empty nodes."""
    logging.info("Action: seed_database")
    spanner.seed_database()
    return ('OK', 200)
