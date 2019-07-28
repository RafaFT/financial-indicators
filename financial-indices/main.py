import logging
import os
import sys

import bcb_api
import excel_writer
import indices_expander
import utils


# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create stream handler
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(module)s] [%(funcName)s] [%(lineno)d] [%(message)s]'
)
sh.setFormatter(formatter)
logger.addHandler(sh)

logging_path = utils.create_log_path()
if logging_path is not None:
    # Create file handler
    fh = logging.FileHandler(os.path.join(logging_path, 'financial-indices.log'), 'w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def handle_exception(exc_type, exc_value, exc_traceback):
    """ Function designed to override the sys.excepthook function, which
    is the last function called before an uncaught exception is raised,
    and log the exception information before quitting.
    """
    logger.critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


@utils.log_func_time(logger, 20)
def main():
    logger.info('Starting program...')

    working_indices = (
        11,
        12,
        226,
        433,
    )

    api = bcb_api.FinancialIndicesApi()
    expander = indices_expander.IndicesExpander()
    workbook = excel_writer.IndicesWorkbook(
        path_to_file=utils.bundle_dir,
        filename='financial-indices.xlsx'
    )

    updated_indices = False
    for indices_code in working_indices:
        wb_last_date = workbook.get_last_indices_date(indices_code)
        api.set_indices_records({indices_code: (wb_last_date, None)})
        api_last_date = api.get_latest_date(indices_code)

        if wb_last_date == api_last_date:
            logger.info(f'Indices code {indices_code} is up-to-date')
            continue
        else:
            logger.info(f'Updating Indices code {indices_code}')
            updated_indices = True
            expanded_indices = expander.get_expanded_indices(
                indices_code, api[indices_code]
            )
            workbook.write_records(indices_code,
                                   expanded_indices,
                                   api_last_date)

    if updated_indices:
        workbook.save()


if __name__ == '__main__':
    sys.excepthook = handle_exception
    main()
