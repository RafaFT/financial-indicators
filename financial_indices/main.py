import logging
import os

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
    fh = logging.FileHandler(os.path.join(logging_path, 'logs'), 'w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


@utils.log_func_time(logger, 20)
def main():
    logger.info('Starting program...')

    working_indices = (
        11,
        12,
        226,
        433,
    )

    logging.info(f'Trying to create/update indices: {working_indices}')

    api = bcb_api.FinancialIndicesApi()
    expander = indices_expander.IndicesExpander()
    workbook = excel_writer.IndicesWorkbook()

    for indices_code in working_indices:
        wb_last_date = workbook.get_last_indices_date(indices_code)
        api.set_indices_records({indices_code: (wb_last_date, None)})
        api_last_date = api.get_latest_date(indices_code)

        if wb_last_date == api_last_date:
            continue

        expanded_indices = expander.get_expanded_indices(indices_code, api[indices_code])
        workbook.write_records(indices_code, expanded_indices, api_last_date)

    workbook.save()


if __name__ == '__main__':
    main()
