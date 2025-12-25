import base64
import functions_framework
import logging

logging.getLogger().setLevel(logging.INFO)

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def handle_feed_event(cloud_event):
    # Currently, simply logs the event but it can be used for any cloud side processing.
    pubsub_message = cloud_event.data['message']
    logging.info(f"Received Pub/Sub message: {pubsub_message}")
    try:
        data_bytes = base64.b64decode(pubsub_message["data"])
        notification_json = data_bytes.decode("utf-8")
        logging.info(f"Notification content: {notification_json}")
    except Exception as e:
        logging.error(f"Error decoding message data: {e}")

    attributes = pubsub_message.get('attributes', {})
    if attributes.get('transfer_status') == 'TRANSFER_COMPLETED':
        feed_type = attributes.get('feedType')
        if feed_type == 'Schema':
            logging.info('Updating schema import status')
        elif feed_type == 'Place':
            logging.info('Updating place import status')
        else:
            logging.info('Unknown feed type')
