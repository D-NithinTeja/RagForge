# # Testing ragforge.config
# from ragforge.config import settings

# print(f"Project Name: {settings.APP_NAME}")
# print(f"Database URL: {settings.DATABASE_URL}")

# print("*" * 70)

# # Testing logging
# import logging

# from ragforge.config import settings
# from ragforge.core.logger import setup_logging

# setup_logging()

# logger = logging.getLogger("RAGForge.TESTING.Logging")

# logger.info(f"Project Name: {settings.APP_NAME}")
# logger.debug("Check")
# logger.warning("Check")

# print("*" * 70)

import logging

from ragforge.core.exceptions import AppError, DocumentNotFound, FileValidationError
from ragforge.core.logger import setup_logging

setup_logging()
logger = logging.getLogger("RAGForge.TESTING.Exceptions")


def simulate_pipeline_operation(action_code: int):
    doc_id = 2
    if action_code == 1:
        raise DocumentNotFound()
    elif action_code == 2:
        raise FileValidationError(f"File {doc_id} exceeds 50MB")
    else:
        raise AppError()


for test_id in [1, 2, 3]:
    try:
        simulate_pipeline_operation(test_id)
    except AppError as e:
        logger.error(
            f"Intercepted Exception -> HTTP Status Code: {e.status_code} | Message : {e.message}"
        )
