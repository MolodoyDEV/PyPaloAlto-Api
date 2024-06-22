import logging

logger = logging.getLogger('pypaloalto_api')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s [pypaloalto_api] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
